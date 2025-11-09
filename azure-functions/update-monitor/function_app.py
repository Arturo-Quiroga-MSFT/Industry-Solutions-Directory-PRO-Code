"""
Azure Function: ISD Update Monitor

Owner: Arturo Quiroga, Principal Industry Solutions Architect, Microsoft
Purpose: Timer-triggered function to check for ISD website updates weekly
Last Updated: November 8, 2025

Schedule: Every Monday at 9:00 AM UTC (0 0 9 * * 1)
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import requests
import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create function app
app = func.FunctionApp()


class ISDUpdateMonitor:
    """Monitor ISD website for changes and send notifications."""
    
    def __init__(self):
        """Initialize with Azure credentials and configuration."""
        # Azure Search configuration
        self.search_service = os.getenv('AZURE_SEARCH_SERVICE')
        self.search_endpoint = f"https://{self.search_service}.search.windows.net"
        self.index_name = os.getenv('AZURE_SEARCH_INDEX', 'partner-solutions-integrated')
        
        # Use managed identity in Azure, API key for local testing
        search_key = os.getenv('AZURE_SEARCH_KEY')
        if search_key:
            credential = AzureKeyCredential(search_key)
        else:
            credential = DefaultAzureCredential()
        
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=credential
        )
        
        # ISD API configuration
        self.isd_api_base = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
        
        # Email notification configuration
        self.notification_email_to = os.getenv('NOTIFICATION_EMAIL_TO')
        self.notification_email_from = os.getenv('NOTIFICATION_EMAIL_FROM', 'DoNotReply@azurecomm.net')
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')  # Optional: for SendGrid
    
    def fetch_isd_solutions(self) -> Dict[str, Dict]:
        """Fetch all current solutions from ISD website."""
        logger.info("Fetching current solutions from ISD website...")
        
        try:
            # Fetch menu structure
            menu_url = f"{self.isd_api_base}/getMenu"
            response = requests.get(menu_url, timeout=30)
            response.raise_for_status()
            menu_data = response.json()
            
            solutions = {}
            industries = menu_data if isinstance(menu_data, list) else menu_data.get("industryMenu", [])
            
            # Extract solutions by fetching each theme
            for industry in industries:
                industry_name = industry.get("industryName", "Unknown")
                
                for theme in industry.get("subIndustries", []):
                    theme_slug = theme.get("industryThemeSlug")
                    
                    if not theme_slug:
                        continue
                    
                    # Fetch solutions for this theme
                    theme_url = f"{self.isd_api_base}/GetThemeDetalsByViewId"
                    try:
                        theme_response = requests.get(theme_url, params={"slug": theme_slug}, timeout=30)
                        theme_response.raise_for_status()
                        theme_data = theme_response.json()
                        
                        # Process solution areas
                        for area in theme_data.get("themeSolutionAreas", []):
                            for item in area.get("partnerSolutions", []):
                                solution_id = item.get("partnerSolutionId", "")
                                if not solution_id:
                                    continue
                                
                                title = item.get("solutionName", "")
                                partner = item.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                                
                                # Create content hash for change detection
                                content = json.dumps(item, sort_keys=True)
                                content_hash = hashlib.md5(content.encode()).hexdigest()
                                
                                solutions[solution_id] = {
                                    "id": solution_id,
                                    "title": title,
                                    "partner": partner,
                                    "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{item.get('partnerSolutionSlug', '')}",
                                    "content_hash": content_hash,
                                    "industry": industry_name,
                                    "raw_data": item
                                }
                        
                        # Process spotlight solutions
                        for item in theme_data.get("spotLightPartnerSolutions", []):
                            solution_id = item.get("partnerSolutionId", "")
                            if not solution_id:
                                continue
                            
                            title = item.get("solutionName", "")
                            partner = item.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                            
                            content = json.dumps(item, sort_keys=True)
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            
                            solutions[solution_id] = {
                                "id": solution_id,
                                "title": title,
                                "partner": partner,
                                "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{item.get('partnerSolutionSlug', '')}",
                                "content_hash": content_hash,
                                "industry": industry_name,
                                "raw_data": item
                            }
                            
                    except Exception as e:
                        logger.warning(f"Error fetching theme {theme_slug}: {e}")
                        continue
            
            logger.info(f"Found {len(solutions)} solutions on ISD website")
            return solutions
            
        except Exception as e:
            logger.error(f"Error fetching ISD solutions: {e}")
            raise
    
    def fetch_indexed_solutions(self) -> Dict[str, Dict]:
        """Fetch all solutions currently in the search index."""
        logger.info("Fetching solutions from search index...")
        
        try:
            indexed = {}
            
            # Search for all documents - using correct field names
            results = self.search_client.search(
                search_text="*",
                select=["id", "solution_name", "partner_name", "solution_url", "chunk_text"],
                include_total_count=True,
                top=1000  # Adjust if you have more than 1000 unique solutions
            )
            
            for result in results:
                solution_id = result.get("id", "")
                if solution_id:
                    # Create content hash from indexed content
                    content = result.get("chunk_text") or ""
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    indexed[solution_id] = {
                        "id": solution_id,
                        "title": result.get("solution_name") or "",
                        "partner": result.get("partner_name") or "",
                        "url": result.get("solution_url") or "",
                        "content_hash": content_hash
                    }
            
            logger.info(f"Found {len(indexed)} unique solutions in index")
            return indexed
            
        except Exception as e:
            logger.error(f"Error fetching indexed solutions: {e}")
            raise
    
    def compare_solutions(
        self, 
        isd_solutions: Dict[str, Dict], 
        indexed_solutions: Dict[str, Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare ISD solutions with indexed solutions."""
        logger.info("Comparing ISD website with search index...")
        
        isd_ids = set(isd_solutions.keys())
        indexed_ids = set(indexed_solutions.keys())
        
        # Find new solutions (in ISD but not in index)
        new_ids = isd_ids - indexed_ids
        new_solutions = [isd_solutions[sid] for sid in new_ids]
        
        # Find removed solutions (in index but not in ISD)
        removed_ids = indexed_ids - isd_ids
        removed_solutions = [indexed_solutions[sid] for sid in removed_ids]
        
        # Find modified solutions (different content hash)
        modified_solutions = []
        common_ids = isd_ids & indexed_ids
        
        for sid in common_ids:
            if isd_solutions[sid]["content_hash"] != indexed_solutions[sid]["content_hash"]:
                modified_solutions.append({
                    "id": sid,
                    "title": isd_solutions[sid]["title"],
                    "partner": isd_solutions[sid]["partner"],
                    "url": isd_solutions[sid]["url"],
                    "industry": isd_solutions[sid].get("industry", "Unknown")
                })
        
        return new_solutions, modified_solutions, removed_solutions
    
    def send_email_notification(self, new: List[Dict], modified: List[Dict], removed: List[Dict]):
        """Send email notification using SMTP or SendGrid."""
        if not self.notification_email_to:
            logger.info("Notification email not configured, skipping notification")
            return
        
        total_changes = len(new) + len(modified) + len(removed)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Build email content
        if total_changes == 0:
            subject = "✅ ISD Update Check: No Changes"
            body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #00AA00;">✅ ISD Update Check Complete</h2>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p>No changes detected - the search index is up to date with the ISD website.</p>
    <hr style="border: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 12px;">
        This is an automated message from the ISD Update Monitor.<br>
        Azure Function: Industry Solutions Directory Update Monitor
    </p>
</body>
</html>
"""
        else:
            subject = f"⚠️ ISD Update Check: {total_changes} Changes Detected"
            
            # Build detailed lists
            new_html = ""
            if new:
                new_list = "".join([f"<li>{s['title']} <em>({s['partner']})</em></li>" for s in new[:10]])
                if len(new) > 10:
                    new_list += f"<li><em>... and {len(new) - 10} more</em></li>"
                new_html = f"""
    <h3 style="color: #0078D4;">🆕 New Solutions: {len(new)}</h3>
    <ul>{new_list}</ul>
"""
            
            modified_html = ""
            if modified:
                mod_list = "".join([f"<li>{s['title']} <em>({s['partner']})</em></li>" for s in modified[:10]])
                if len(modified) > 10:
                    mod_list += f"<li><em>... and {len(modified) - 10} more</em></li>"
                modified_html = f"""
    <h3 style="color: #FF8C00;">✏️ Modified Solutions: {len(modified)}</h3>
    <ul>{mod_list}</ul>
"""
            
            removed_html = ""
            if removed:
                rem_list = "".join([f"<li>{s['title']} <em>({s['partner']})</em></li>" for s in removed[:10]])
                if len(removed) > 10:
                    rem_list += f"<li><em>... and {len(removed) - 10} more</em></li>"
                removed_html = f"""
    <h3 style="color: #CC0000;">🗑️ Removed Solutions: {len(removed)}</h3>
    <ul>{rem_list}</ul>
"""
            
            body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #FF8C00;">📊 ISD Website Update Detected</h2>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Total Changes:</strong> {total_changes}</p>
    
    <table style="margin: 20px 0; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>🆕 New:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{len(new)}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>✏️ Modified:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{len(modified)}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>🗑️ Removed:</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{len(removed)}</td>
        </tr>
    </table>
    
    {new_html}
    {modified_html}
    {removed_html}
    
    <hr style="border: 1px solid #eee; margin: 20px 0;">
    
    <p><strong>📝 Recommended Action:</strong></p>
    <p>Re-run the data ingestion pipeline to update the search index with these changes.</p>
    
    <p><a href="https://solutions.microsoftindustryinsights.com" style="color: #0078D4;">View ISD Website</a></p>
    
    <hr style="border: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 12px;">
        This is an automated message from the ISD Update Monitor.<br>
        Azure Function: Industry Solutions Directory Update Monitor
    </p>
</body>
</html>
"""
        
        # Send email using SendGrid if API key is configured
        if self.sendgrid_api_key:
            self._send_via_sendgrid(subject, body)
        else:
            # Log email content (for testing without actual email service)
            logger.info(f"Email notification ready (no email service configured)")
            logger.info(f"Subject: {subject}")
            logger.info(f"To: {self.notification_email_to}")
            logger.info(f"Changes: {total_changes}")
    
    def _send_via_sendgrid(self, subject: str, body: str):
        """Send email via SendGrid API."""
        try:
            sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "personalizations": [{
                    "to": [{"email": self.notification_email_to}],
                    "subject": subject
                }],
                "from": {"email": self.notification_email_from},
                "content": [{
                    "type": "text/html",
                    "value": body
                }]
            }
            
            response = requests.post(sendgrid_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Email notification sent successfully to {self.notification_email_to}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def send_failure_notification(self, error: Exception):
        """Send failure notification via email."""
        if not self.notification_email_to:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        subject = "❌ ISD Update Check Failed"
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #CC0000;">❌ ISD Update Check Failed</h2>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Error:</strong></p>
    <pre style="background: #f5f5f5; padding: 15px; border-left: 3px solid #CC0000;">{str(error)}</pre>
    <hr style="border: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 12px;">
        This is an automated error notification from the ISD Update Monitor.<br>
        Please check the Azure Function logs for more details.
    </p>
</body>
</html>
"""
        
        try:
            if self.sendgrid_api_key:
                self._send_via_sendgrid(subject, body)
            else:
                logger.error(f"Failed to send failure notification: No email service configured")
        except:
            pass  # Ignore failures in failure notification
    
    def run_check(self) -> Dict:
        """Run the update check and return results."""
        try:
            # Fetch current data
            isd_solutions = self.fetch_isd_solutions()
            indexed_solutions = self.fetch_indexed_solutions()
            
            # Compare
            new, modified, removed = self.compare_solutions(isd_solutions, indexed_solutions)
            
            # Send notification
            self.send_email_notification(new, modified, removed)
            
            # Return summary
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "new_count": len(new),
                "modified_count": len(modified),
                "removed_count": len(removed),
                "total_changes": len(new) + len(modified) + len(removed),
                "isd_total": len(isd_solutions),
                "index_total": len(indexed_solutions)
            }
            
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            self.send_failure_notification(e)
            raise


@app.timer_trigger(
    schedule="0 0 9 * * 1",  # Every Monday at 9:00 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def isd_update_monitor(timer: func.TimerRequest) -> None:
    """
    Timer-triggered function to check for ISD website updates.
    
    Schedule: Every Monday at 9:00 AM UTC
    CRON: 0 0 9 * * 1 (sec min hour day month dayOfWeek)
    """
    if timer.past_due:
        logger.info('The timer is past due!')
    
    logger.info('ISD Update Monitor function started')
    
    try:
        monitor = ISDUpdateMonitor()
        result = monitor.run_check()
        
        logger.info(f"Update check completed successfully: {result}")
        logger.info(f"Total changes detected: {result['total_changes']}")
        
    except Exception as e:
        logger.error(f"Update check failed: {e}", exc_info=True)
        raise


@app.function_name(name="isd_update_check_http")
@app.route(route="update-check", methods=["GET", "POST"], auth_level=func.AuthLevel.FUNCTION)
def isd_update_check_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function for manual update checks.
    Useful for testing or triggering checks on-demand.
    """
    logger.info('HTTP trigger - ISD Update Check requested')
    
    try:
        monitor = ISDUpdateMonitor()
        result = monitor.run_check()
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Update check failed: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
