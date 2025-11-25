# Merge Queue Statistics

This branch contains automated merge queue statistics collected every 30 minutes.

## Average PRs by Hour of Day (PST)

### Last Day
![PRs by Hour - Last Day](prs_by_hour_last_day.png)

### Last Week
![PRs by Hour - Last Week](prs_by_hour_last_week.png)

### Last Month
![PRs by Hour - Last Month](prs_by_hour_last_month.png)

### All Time
![PRs by Hour - All Time](prs_by_hour_all.png)

## Files

- `summarized.csv` - CSV summary of all collected statistics
- `prs_by_hour_*.png` - Graphs showing average PRs by hour of day for different time periods
- `stats/YYYY-MM/merge_queue_YYYYMMDD_HHMMSS.json` - Individual JSON stats files organized by month
