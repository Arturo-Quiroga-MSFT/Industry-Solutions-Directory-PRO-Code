#!/bin/bash
# Package Teams apps into .zip files for sideloading or admin upload
set -e
cd "$(dirname "$0")"

for app in seller customer; do
    echo "Packaging $app..."
    (cd "$app" && zip -j "../isd-${app}-teams-app.zip" manifest.json color.png outline.png)
done

echo ""
echo "Done! Created:"
ls -lh isd-*-teams-app.zip
