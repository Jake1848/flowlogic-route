#!/bin/sh
set -e

# Replace environment variables in JavaScript files
# This allows runtime configuration without rebuilding the image

if [ -n "$REACT_APP_API_URL" ]; then
    echo "Setting REACT_APP_API_URL to: $REACT_APP_API_URL"
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|REACT_APP_API_URL_PLACEHOLDER|$REACT_APP_API_URL|g" {} \;
fi

if [ -n "$REACT_APP_MAPBOX_TOKEN" ]; then
    echo "Setting REACT_APP_MAPBOX_TOKEN"
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|REACT_APP_MAPBOX_TOKEN_PLACEHOLDER|$REACT_APP_MAPBOX_TOKEN|g" {} \;
fi

if [ -n "$REACT_APP_SITE_NAME" ]; then
    echo "Setting REACT_APP_SITE_NAME to: $REACT_APP_SITE_NAME"
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|REACT_APP_SITE_NAME_PLACEHOLDER|$REACT_APP_SITE_NAME|g" {} \;
fi

echo "Starting Nginx..."
exec "$@"