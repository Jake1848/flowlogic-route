#!/bin/bash
# FlowLogic RouteAI PostgreSQL Backup Script
# Performs automated backups with rotation and optional S3 upload

set -e

# Configuration from environment variables
POSTGRES_DB=${POSTGRES_DB:-flowlogic}
POSTGRES_USER=${POSTGRES_USER:-postgres}
PGPASSWORD=${POSTGRES_PASSWORD:-password}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
BACKUP_DIR=${BACKUP_DIR:-/backups}
S3_BACKUP_BUCKET=${S3_BACKUP_BUCKET:-}

# Timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="flowlogic_backup_${TIMESTAMP}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting backup process at $(date)"

# Create database dump
echo "Creating database dump..."
pg_dump -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    > "$BACKUP_DIR/${BACKUP_NAME}.dump"

# Create SQL backup as well
echo "Creating SQL backup..."
pg_dump -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --no-owner \
    --no-privileges \
    > "$BACKUP_DIR/${BACKUP_NAME}.sql"

# Compress SQL backup
gzip "$BACKUP_DIR/${BACKUP_NAME}.sql"

# Create backup manifest
cat > "$BACKUP_DIR/${BACKUP_NAME}.manifest" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "database": "${POSTGRES_DB}",
    "created_at": "$(date -Iseconds)",
    "files": [
        "${BACKUP_NAME}.dump",
        "${BACKUP_NAME}.sql.gz"
    ],
    "sizes": {
        "dump": "$(stat -c%s "$BACKUP_DIR/${BACKUP_NAME}.dump" 2>/dev/null || echo 0)",
        "sql_gz": "$(stat -c%s "$BACKUP_DIR/${BACKUP_NAME}.sql.gz" 2>/dev/null || echo 0)"
    }
}
EOF

echo "Backup created successfully:"
echo "- Dump file: ${BACKUP_NAME}.dump"
echo "- SQL file: ${BACKUP_NAME}.sql.gz"
echo "- Manifest: ${BACKUP_NAME}.manifest"

# Upload to S3 if configured
if [ -n "$S3_BACKUP_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Uploading backup to S3..."
    
    # Check if AWS CLI is available
    if command -v aws >/dev/null 2>&1; then
        aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.dump" "s3://$S3_BACKUP_BUCKET/backups/${BACKUP_NAME}.dump"
        aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.sql.gz" "s3://$S3_BACKUP_BUCKET/backups/${BACKUP_NAME}.sql.gz"
        aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.manifest" "s3://$S3_BACKUP_BUCKET/backups/${BACKUP_NAME}.manifest"
        echo "Backup uploaded to S3 successfully"
    else
        echo "Warning: AWS CLI not available, skipping S3 upload"
    fi
fi

# Clean up old backups
echo "Cleaning up old backups (older than $BACKUP_RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "flowlogic_backup_*" -type f -mtime +$BACKUP_RETENTION_DAYS -delete

# Clean up old S3 backups if configured
if [ -n "$S3_BACKUP_BUCKET" ] && command -v aws >/dev/null 2>&1; then
    echo "Cleaning up old S3 backups..."
    # List and delete old S3 backups (this is a simplified approach)
    CUTOFF_DATE=$(date -d "$BACKUP_RETENTION_DAYS days ago" +%Y%m%d)
    aws s3 ls "s3://$S3_BACKUP_BUCKET/backups/" | \
        awk '{print $4}' | \
        grep "flowlogic_backup_" | \
        while read -r file; do
            file_date=$(echo "$file" | sed 's/flowlogic_backup_\([0-9]\{8\}\).*/\1/')
            if [ "$file_date" -lt "$CUTOFF_DATE" ]; then
                aws s3 rm "s3://$S3_BACKUP_BUCKET/backups/$file"
                echo "Deleted old S3 backup: $file"
            fi
        done
fi

# Verify backup integrity
echo "Verifying backup integrity..."
if pg_restore --list "$BACKUP_DIR/${BACKUP_NAME}.dump" >/dev/null 2>&1; then
    echo "✓ Backup verification successful"
else
    echo "✗ Backup verification failed!"
    exit 1
fi

# Summary
BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.dump" | cut -f1)
echo "Backup completed successfully at $(date)"
echo "Backup size: $BACKUP_SIZE"
echo "Location: $BACKUP_DIR/${BACKUP_NAME}.*"

# Create a symlink to latest backup
ln -sf "${BACKUP_NAME}.dump" "$BACKUP_DIR/latest.dump"
ln -sf "${BACKUP_NAME}.sql.gz" "$BACKUP_DIR/latest.sql.gz"
ln -sf "${BACKUP_NAME}.manifest" "$BACKUP_DIR/latest.manifest"

echo "Latest backup symlinks updated"

# Send notification if webhook URL is configured
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"message\": \"FlowLogic backup completed successfully\",
            \"backup_name\": \"$BACKUP_NAME\",
            \"size\": \"$BACKUP_SIZE\",
            \"timestamp\": \"$(date -Iseconds)\"
        }" \
        --silent --show-error || echo "Warning: Failed to send backup notification"
fi

echo "Backup process completed successfully"