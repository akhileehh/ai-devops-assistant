import boto3, os
from datetime import datetime, timedelta
from gemini_helper import explain_error

#read keys from env
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

ec2 = session.client("ec2")

def list_ec2():
    instances = ec2.describe_instances()["Reservations"]
    if not instances:
        return "No EC2 instances found."
    
    msg = "**EC2 Instances:**\n"
    for r in instances:
        for i in r["Instances"]:
            #Name tag
            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "No Name")

            #OS info
            platform = i.get("PlatformDetails") or i.get("Platform") or "Linux/Unix"
            msg += f"• **{name}**  →  `{i['InstanceId']}`  ({i['InstanceType']})  –  **{i['State']['Name']}**  –  *{platform}*\n"

    return msg

# S3
def list_s3():
    s3 = session.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    if not buckets:
        return "No S3 buckets found."
    return "**S3 Buckets:**\n" + "\n".join(f"• `{b['Name']}`  (created {b['CreationDate'].strftime('%Y-%m-%d')})" for b in buckets)

# Service Health
def aws_health():
    #Free-tier fallback
    ec2 = session.client("ec2")
    cw  = session.client("cloudwatch")
    try:
        # EC2 overall state
        instances = ec2.describe_instances()["Reservations"]
        running   = sum(1 for r in instances for i in r["Instances"] if i["State"]["Name"] == "running")
        stopped   = sum(1 for r in instances for i in r["Instances"] if i["State"]["Name"] == "stopped")

        # Alarm count in last 24 h
        alarms = cw.describe_alarms(StateValue="ALARM")["MetricAlarms"]

        msg  = "**AWS Health **\n"
        msg += f"🟢 Running EC2: {running} 🔴 Stopped: {stopped}\n"
        msg += f"🚨 CloudWatch ALARMs: {len(alarms)}\n"
        if alarms:
            msg += "\n".join(f"  • {a['AlarmName']}" for a in alarms[:3])
        return msg
    except Exception as e:
        return f"Health check error: {e}"
    
#CloudWatch Logs 
def analyze_logs(log_group, hours=1):
    logs = session.client("logs")
    end = int(datetime.now(datetime.timezone.utc).timestamp() * 1000)
    start = end - hours * 3600 * 1000
    streams = logs.describe_log_groups(logGroupNamePrefix=log_group)["logGroups"]
    if not streams:
        return "Log group not found."
    # Grab last 50 log events
    events = logs.filter_log_events(logGroupName=log_group, startTime=start, endTime=end, limit=50)["events"]
    if not events:
        return f"No logs in the last {hours}h."
    # Build short summary for Gemini
    text = "\n".join(e["message"] for e in events)
    prompt = f"Summarize key errors, warnings, and one fix from these logs:\n{text}"
    return explain_error(prompt)  # reuse Gemini helper

def fetch_cost_json(days: int = 7):
    """Returns raw Cost-Explorer dict or None if not enabled."""
    try:
        ce = session.client("ce", region_name="us-east-1")
        return ce.get_cost_and_usage(
            TimePeriod={
                "Start": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "End": datetime.utcnow().strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["BlendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
    except Exception:
        return None