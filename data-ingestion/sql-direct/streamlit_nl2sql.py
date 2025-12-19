#!/usr/bin/env python3
"""
Streamlit UI for NL2SQL Industry Solutions Explorer
Direct SQL-based approach using dbo.vw_ISDSolution_All view
"""

import streamlit as st
import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from nl2sql_pipeline import NL2SQLPipeline

# Page configuration
st.set_page_config(
    page_title="ISD NL2SQL Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    .app-header {
        background: linear-gradient(90deg, #0078d4 0%, #50e6ff 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .app-header h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0;
        font-weight: 600;
    }
    
    .sql-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        border-left: 4px solid #0078d4;
        margin: 1rem 0;
    }
    
    .safety-banner {
        background-color: #fff4e5;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .comparison-badge {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to strip HTML tags
def strip_html(text):
    """Remove HTML tags from text"""
    if pd.isna(text) or text is None:
        return text
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text_without_tags = re.sub(clean, '', str(text))
    # Replace multiple spaces/newlines with single space
    text_without_tags = re.sub(r'\s+', ' ', text_without_tags)
    return text_without_tags.strip()

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = NL2SQLPipeline()

if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'conversation_summary' not in st.session_state:
    st.session_state.conversation_summary = None

# Header
st.markdown("""
<div class="app-header">
    <h1>🔍 Industry Solutions Directory</h1>
    <p>Natural Language to SQL Explorer | Direct Database Access</p>
</div>
""", unsafe_allow_html=True)

# Safety banner
st.markdown("""
<div class="safety-banner">
    ⚠️ <strong>Production Database - READ-ONLY Mode</strong><br>
    All queries are validated and executed with multiple safety layers. No write operations allowed.
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Quick Start")
    
    # Approach comparison
    st.markdown("#### 📊 Approach Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**API-based**")
        st.caption("• REST API")
        st.caption("• 535 solutions")
        st.caption("• Limited filters")
    with col2:
        st.markdown("**NL2SQL** 🆕")
        st.caption("• Direct SQL")
        st.caption("• 5,118 rows")
        st.caption("• Full flexibility")
    
    st.markdown("---")
    
    # Example queries
    st.markdown("### 💡 Example Questions")
    
    example_categories = {
        "🏥 Healthcare": [
            "Show me healthcare AI solutions",
            "Find healthcare solutions with marketplace links",
            "Which partners have the most healthcare solutions?",
            "Compare AI vs Security solutions in healthcare"
        ],
        "💰 Financial Services": [
            "Show financial services security solutions",
            "Find fintech AI solutions",
            "Which partners serve both financial services and healthcare?",
            "List financial solutions with special offers"
        ],
        "🏭 Manufacturing": [
            "Show manufacturing cloud solutions",
            "Find IoT solutions for manufacturing",
            "Which partners serve manufacturing?",
            "Compare manufacturing solutions by technology area"
        ],
        "🤖 Agentic AI Queries": [
            "Which industries have the least AI coverage and represent opportunities?",
            "Show me the technology gap analysis by industry",
            "Find partners with multi-industry expertise",
            "What percentage of solutions have marketplace links by industry?",
            "Identify solution areas with low partner participation",
            "Compare partner market share across industries"
        ],
        "📊 Business Intelligence": [
            "Show market penetration by technology area and industry",
            "Which partners are leaders in multiple technology areas?",
            "Find underserved industries by solution count",
            "Compare solution distribution across geographies",
            "Show partner portfolio diversity analysis",
            "Identify industries with most competition"
        ],
        "🎯 Strategic Analysis": [
            "Which industry-technology combinations have the most solutions?",
            "Find white spaces - industries with fewest security solutions",
            "Compare average solutions per partner by industry",
            "Show technology adoption trends by industry",
            "Identify partners with broadest geographic reach",
            "Find industries dominated by few partners"
        ],
        "🔍 Data Quality": [
            "Show solutions missing marketplace links",
            "Find solutions without special offers",
            "List solutions missing resource links",
            "Count incomplete solution profiles by partner",
            "Show data completeness by industry",
            "Find partners with incomplete solution data"
        ],
        "📈 Trend Analysis": [
            "Show solution distribution by sub-industry",
            "Compare Cloud vs AI solution counts by industry",
            "Find industries with balanced technology coverage",
            "Show partner concentration by technology area",
            "Identify emerging solution categories",
            "Compare solution complexity by industry"
        ]
    }
    
    selected_category = st.selectbox(
        "Select Category",
        list(example_categories.keys()),
        label_visibility="collapsed"
    )
    
    for question in example_categories[selected_category]:
        if st.button(question, key=f"btn_{question}"):
            st.session_state.selected_question = question
            st.rerun()
    
    st.markdown("---")
    
    # Query history
    st.markdown("### 📝 Query History")
    if st.session_state.query_history:
        for i, query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"{i}. {query['natural_query'][:40]}..."):
                st.caption(f"⏰ {query['timestamp']}")
                st.caption(f"📊 {query['row_count']} rows")
                if st.button("🔄 Re-run", key=f"rerun_{i}"):
                    st.session_state.selected_question = query['natural_query']
                    st.rerun()
    else:
        st.caption("No queries yet")
    
    if st.session_state.query_history:
        if st.button("💾 Export History"):
            history_json = json.dumps(st.session_state.query_history, indent=2)
            st.download_button(
                "⬇️ Download JSON",
                data=history_json,
                file_name=f"nl2sql_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Main content area
st.markdown("### 💬 Ask a Question")

# Handle selected question from sidebar - execute immediately
if 'selected_question' in st.session_state and st.session_state.selected_question:
    selected_q = st.session_state.selected_question
    st.session_state.selected_question = None  # Clear it
    
    # Execute immediately
    with st.spinner("🤖 Generating SQL..."):
        sql_result = st.session_state.pipeline.generate_sql(selected_q)
        
        if sql_result['sql']:
            is_valid = st.session_state.pipeline.validate_sql(sql_result['sql'])
            
            if is_valid:
                with st.spinner("📊 Executing query..."):
                    result = st.session_state.pipeline.execute_sql(sql_result['sql'])
                    
                    st.session_state.current_result = {
                        'question': selected_q,
                        'sql': sql_result['sql'],
                        'explanation': sql_result['explanation'],
                        'confidence': sql_result['confidence'],
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.query_history.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'natural_query': selected_q,
                        'sql': sql_result['sql'],
                        'row_count': result['row_count'],
                        'success': result['error'] is None
                    })
                    
                    # Add to chat messages
                    st.session_state.chat_messages.append({
                        'role': 'user',
                        'content': selected_q,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': f"Found {result['row_count']} results",
                        'sql': sql_result['sql'],
                        'row_count': result['row_count'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    st.rerun()

# Question input
question = st.text_input(
    "Enter your question in natural language:",
    placeholder="e.g., Show me the top 10 healthcare AI solutions",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    execute_btn = st.button("🚀 Execute Query", type="primary")
with col2:
    if st.session_state.current_result:
        clear_btn = st.button("🗑️ Clear Results")
        if clear_btn:
            st.session_state.current_result = None
            st.rerun()
with col3:
    show_sql = st.checkbox("Show SQL", value=True)

if execute_btn and question:
    with st.spinner("🤖 Generating SQL..."):
        # Generate SQL
        sql_result = st.session_state.pipeline.generate_sql(question)
        
        if sql_result['sql']:
            # Validate
            is_valid = st.session_state.pipeline.validate_sql(sql_result['sql'])
            
            if is_valid:
                with st.spinner("📊 Executing query..."):
                    # Execute
                    result = st.session_state.pipeline.execute_sql(sql_result['sql'])
                    
                    # Store result
                    st.session_state.current_result = {
                        'question': question,
                        'sql': sql_result['sql'],
                        'explanation': sql_result['explanation'],
                        'confidence': sql_result['confidence'],
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Add to history
                    st.session_state.query_history.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'natural_query': question,
                        'sql': sql_result['sql'],
                        'row_count': result['row_count'],
                        'success': result['error'] is None
                    })
                    
                    # Add to chat messages
                    st.session_state.chat_messages.append({
                        'role': 'user',
                        'content': question,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': f"Found {result['row_count']} results",
                        'sql': sql_result['sql'],
                        'row_count': result['row_count'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    st.rerun()
            else:
                st.error("❌ Query validation failed. SQL contains unsafe operations.")
        else:
            st.error("❌ Failed to generate SQL query.")

# Conversation History
if st.session_state.chat_messages:
        with st.expander("💬 Conversation History", expanded=False):
            for msg in st.session_state.chat_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; color: white;'>
                        <strong>You:</strong> {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: rgba(255, 255, 255, 0.05); 
                                border-left: 4px solid #0078d4; padding: 1rem; 
                                border-radius: 0.5rem; margin: 0.5rem 0;'>
                        <strong>Assistant:</strong> {msg['content']}<br>
                        <small>📊 {msg.get('row_count', 0)} rows returned</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Conversation actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 Generate Summary"):
                    # Generate summary
                    summary_text = f"""## Conversation Summary
                    
**Total Queries**: {len([m for m in st.session_state.chat_messages if m['role'] == 'user'])}  
**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Questions Asked:
"""
                    for i, msg in enumerate([m for m in st.session_state.chat_messages if m['role'] == 'user'], 1):
                        summary_text += f"{i}. {msg['content']}\n"
                    
                    summary_text += "\n### Key Insights:\n"
                    for msg in st.session_state.chat_messages:
                        if msg['role'] == 'assistant' and msg.get('row_count', 0) > 0:
                            summary_text += f"- Found {msg['row_count']} results\n"
                    
                    st.session_state.conversation_summary = summary_text
                    st.rerun()
            
            with col2:
                if st.session_state.conversation_summary:
                    st.download_button(
                        "⬇️ Download Summary",
                        data=st.session_state.conversation_summary,
                        file_name=f"conversation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
            
            with col3:
                # Export full conversation
                conversation_json = json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'messages': st.session_state.chat_messages,
                    'query_count': len([m for m in st.session_state.chat_messages if m['role'] == 'user'])
                }, indent=2)
                
                st.download_button(
                    "⬇️ Export Chat",
                    data=conversation_json,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Display summary if generated
            if st.session_state.conversation_summary:
                with st.expander("📄 Summary", expanded=True):
                    st.markdown(st.session_state.conversation_summary)

# Display results
if st.session_state.current_result:
    result_data = st.session_state.current_result
    
    st.markdown("---")
    st.markdown("### 📊 Query Results")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{result_data['result']['row_count']}</h3>
            <p>Rows Returned</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        st.markdown(f"""
        <div class="metric-card">
            <h3>{confidence_color.get(result_data['confidence'], '⚪')} {result_data['confidence'].upper()}</h3>
            <p>Confidence</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(result_data['result']['columns'])}</h3>
            <p>Columns</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ SAFE</h3>
            <p>Read-Only</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Table", "📊 Visualizations", "💡 SQL Query", "📥 Data Export"])
    
    with tab1:
        if result_data['result']['error']:
            st.error(f"❌ Error: {result_data['result']['error']}")
        elif result_data['result']['row_count'] == 0:
            st.warning("⚠️ No results found.")
        else:
            # Convert to DataFrame (convert pyodbc.Row objects to tuples)
            rows_data = [tuple(row) for row in result_data['result']['rows']]
            df = pd.DataFrame(
                rows_data,
                columns=result_data['result']['columns']
            )
            
            # Replace NULL/None with "(Not Set)" for better UX
            df = df.fillna("(Not Set)")
            # Also replace string "NULL" values
            df = df.replace("NULL", "(Not Set)")
            df = df.replace("None", "(Not Set)")
            
            # Clean HTML from description columns
            html_columns = ['solutionDescription', 'industryDescription', 'SubIndustryDescription', 
                          'solAreaDescription', 'orgDescription', 'areaSolutionDescription',
                          'industryThemeDesc', 'solutionPlayDesc', 'resourceLinkDescription']
            
            for col in html_columns:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: strip_html(x) if x != "(Not Set)" else x)
            
            # Truncate long text fields for better display
            for col in df.columns:
                if df[col].dtype == 'object':  # String columns
                    df[col] = df[col].apply(lambda x: str(x)[:200] + '...' if x != "(Not Set)" and len(str(x)) > 200 else x)
            
            # Display DataFrame
            st.dataframe(
                df,
                width='stretch',
                height=400
            )
            
            # Quick stats
            st.markdown("#### 📈 Quick Statistics")
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Total Rows", len(df))
            with stat_cols[1]:
                st.metric("Total Columns", len(df.columns))
            with stat_cols[2]:
                # Count unique values in first column
                if len(df.columns) > 0:
                    unique_count = df[df.columns[0]].nunique()
                    st.metric(f"Unique {df.columns[0]}", unique_count)
            with stat_cols[3]:
                null_count = df.isnull().sum().sum()
                st.metric("NULL Values", null_count)
    
    with tab2:
        # Visualizations tab
        if result_data['result']['error']:
            st.error(f"❌ Error: {result_data['result']['error']}")
        elif result_data['result']['row_count'] == 0:
            st.warning("⚠️ No results to visualize.")
        else:
            # Convert to DataFrame
            rows_data = [tuple(row) for row in result_data['result']['rows']]
            df = pd.DataFrame(
                rows_data,
                columns=result_data['result']['columns']
            )
            
            # Replace NULL/None with "(Not Set)"
            df = df.fillna("(Not Set)")
            df = df.replace("NULL", "(Not Set)")
            df = df.replace("None", "(Not Set)")
            
            # Detect visualization opportunities
            st.markdown("### 📊 Auto-Generated Visualizations")
            
            # Check if data is suitable for visualization
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if len(df.columns) == 2 and len(numeric_cols) == 1:
                # Perfect for bar chart or pie chart (category + count)
                cat_col = [c for c in df.columns if c not in numeric_cols][0]
                val_col = numeric_cols[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Bar Chart")
                    fig_bar = px.bar(
                        df.head(20),  # Limit to top 20 for readability
                        x=cat_col,
                        y=val_col,
                        title=f"{val_col} by {cat_col}",
                        color=val_col,
                        color_continuous_scale='blues'
                    )
                    fig_bar.update_layout(xaxis_tickangle=-45, height=500)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    st.markdown("#### 🥧 Pie Chart")
                    fig_pie = px.pie(
                        df.head(10),  # Top 10 for pie chart
                        values=val_col,
                        names=cat_col,
                        title=f"Distribution of {val_col}"
                    )
                    fig_pie.update_layout(height=500)
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            elif len(numeric_cols) >= 2:
                # Multiple numeric columns - show comparison
                st.markdown("#### 📈 Multi-Metric Comparison")
                
                # Grouped bar chart
                fig_grouped = go.Figure()
                for col in numeric_cols[:5]:  # Max 5 metrics
                    fig_grouped.add_trace(go.Bar(
                        name=col,
                        x=df.index[:20],
                        y=df[col][:20]
                    ))
                
                fig_grouped.update_layout(
                    barmode='group',
                    title="Metric Comparison",
                    height=500
                )
                st.plotly_chart(fig_grouped, use_container_width=True)
            
            elif len(df.columns) >= 3 and len(numeric_cols) >= 1:
                # Multiple dimensions - show different views
                st.markdown("#### 📊 Multi-Dimensional Analysis")
                
                viz_type = st.selectbox(
                    "Choose Visualization",
                    ["Bar Chart", "Horizontal Bar", "Treemap", "Sunburst"]
                )
                
                if len(text_cols) >= 1 and len(numeric_cols) >= 1:
                    cat_col = text_cols[0]
                    val_col = numeric_cols[0]
                    
                    if viz_type == "Bar Chart":
                        fig = px.bar(
                            df.head(20),
                            x=cat_col,
                            y=val_col,
                            color=text_cols[1] if len(text_cols) > 1 else None,
                            title=f"{val_col} by {cat_col}"
                        )
                        fig.update_layout(xaxis_tickangle=-45, height=600)
                        
                    elif viz_type == "Horizontal Bar":
                        fig = px.bar(
                            df.head(20),
                            y=cat_col,
                            x=val_col,
                            orientation='h',
                            color=val_col,
                            title=f"{val_col} by {cat_col}"
                        )
                        fig.update_layout(height=600)
                        
                    elif viz_type == "Treemap":
                        path_cols = text_cols[:2] if len(text_cols) >= 2 else [cat_col]
                        fig = px.treemap(
                            df.head(50),
                            path=path_cols,
                            values=val_col,
                            title=f"Hierarchical View of {val_col}"
                        )
                        fig.update_layout(height=600)
                        
                    else:  # Sunburst
                        path_cols = text_cols[:2] if len(text_cols) >= 2 else [cat_col]
                        fig = px.sunburst(
                            df.head(50),
                            path=path_cols,
                            values=val_col,
                            title=f"Hierarchical Distribution"
                        )
                        fig.update_layout(height=600)
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.info("💡 This data is best viewed in table format. Try queries with counts, sums, or aggregations for automatic visualizations!")
                
                # Still show basic statistics if available
                if len(numeric_cols) > 0:
                    st.markdown("#### 📈 Summary Statistics")
                    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    
    with tab3:
        st.markdown("#### 🔍 Question")
        st.info(result_data['question'])
        
        st.markdown("#### 💡 Explanation")
        st.write(result_data['explanation'])
        
        st.markdown("#### 🔧 Generated SQL")
        st.code(result_data['sql'], language='sql')
        
        st.markdown("#### ✅ Validation Status")
        st.success("Query validated - Safe READ-ONLY operation")
        
        # Copy SQL button
        if st.button("📋 Copy SQL to Clipboard"):
            st.code(result_data['sql'], language='sql')
            st.success("✅ SQL copied! (Use Ctrl+C/Cmd+C to copy from the code block above)")
    
    with tab4:
        st.markdown("#### 💾 Export Options")
        
        if not result_data['result']['error'] and result_data['result']['row_count'] > 0:
            # Convert to DataFrame (convert pyodbc.Row objects to tuples)
            rows_data = [tuple(row) for row in result_data['result']['rows']]
            df = pd.DataFrame(
                rows_data,
                columns=result_data['result']['columns']
            )
            
            # Replace NULL/None with "(Not Set)" for better UX
            df = df.fillna("(Not Set)")
            df = df.replace("NULL", "(Not Set)")
            df = df.replace("None", "(Not Set)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV export
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv,
                    file_name=f"isd_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # JSON export
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    "⬇️ Download JSON",
                    data=json_data,
                    file_name=f"isd_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col3:
                # Excel export
                excel_buffer = pd.io.excel.ExcelWriter('temp.xlsx', engine='openpyxl')
                df.to_excel(excel_buffer, index=False, sheet_name='Results')
                excel_buffer.close()
                
                with open('temp.xlsx', 'rb') as f:
                    excel_data = f.read()
                
                st.download_button(
                    "⬇️ Download Excel",
                    data=excel_data,
                    file_name=f"isd_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Full export with metadata
            st.markdown("---")
            st.markdown("#### 📦 Full Export (with metadata)")
            
            full_export = {
                'metadata': {
                    'timestamp': result_data['timestamp'],
                    'question': result_data['question'],
                    'sql': result_data['sql'],
                    'explanation': result_data['explanation'],
                    'confidence': result_data['confidence'],
                    'row_count': result_data['result']['row_count']
                },
                'data': json.loads(df.to_json(orient='records'))
            }
            
            full_json = json.dumps(full_export, indent=2)
            st.download_button(
                "⬇️ Download Complete Package (JSON)",
                data=full_json,
                file_name=f"isd_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.info("No data to export")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🔒 Safety**: 4-layer READ-ONLY protection")
with col2:
    st.markdown("**📊 Data Source**: dbo.vw_ISDSolution_All (5,118 rows)")
with col3:
    st.markdown("**🤖 LLM**: Azure OpenAI GPT-4.1-mini")
