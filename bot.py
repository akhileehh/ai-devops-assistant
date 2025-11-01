import io
import os, discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# ---- Import helpers ----
from aws_helper import (
    list_ec2 as get_ec2_list,
    list_s3 as get_s3_list,
    aws_health as get_health,
    analyze_logs as get_log_analysis,
    fetch_cost_json as get_cost_data,

)
from gemini_helper import (
    explain_error,
    ai_generate_terraform,
    ai_summarize_cost,
    ai_disclaimer_embed,
    ai_security_audit,
    greet_reply,

)

from metrics_helper import start_metrics_server, track_command, command_counter, command_duration, error_counter

# Start Prometheus metrics endpoint on port 8000
start_metrics_server()


load_dotenv()

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)  # still works for debugging
tree = client.tree #slash command system



#On Ready Event

@client.event
async def on_ready():
    # Set bot status
    await client.change_presence(
        activity=discord.Game(name="by Akhil"),
        status=discord.Status.online
    )

    # Sync slash commands
    try:
        synced = await tree.sync()  # Register commands globally
        print(f"✅ {client.user} is now online with {len(synced)} slash command(s) synced!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")



@client.event
async def on_message(message):
    # Ignore bot’s own messages
    if message.author == client.user:
        return

    content = message.content.lower()

    # ---- Greeting trigger with personalized reply ----
    if any(greet in content for greet in ["hi", "hello", "hey"]) and "i am" in content:
        greet_text = greet_reply(message.content)
        await message.channel.send(greet_text)
        return  

    # ---- Normal greeting/help trigger ----
    if content in ["hi", "hello", "hey", "help", "menu", "start"]:
        await message.channel.send(
            f"👋 Hello {message.author.name}! 🤖 I'm your DevOps assistant, happy to help!\n"
            "**Available Commands:**\n"
            "• `/hello` - Greet the bot\n"
            "• `/generate_terraform` - Create Terraform from text\n"
            "• `/list_ec2` - List EC2 instances\n"
            "• `/costs` - Show AWS cost summary\n"
            "• `/list_s3` - List S3 buckets\n"
            "• `/aws_health` - Check AWS service health\n"
            "• `/analyze_logs` - Summarize CloudWatch logs\n"
            "• `/explain` - Explain AWS errors\n"
            "• `/security` - Quick security audit\n"
            "• `/disclaimer` - View bot disclaimer\n"
            "• `/menu` - Toggle command menu\n"
        )
        return

    # Let slash commands still work
    await client.process_commands(message)




@tree.command(name="hello", description="Say hi to your assistant")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
         "**👋 Hello!**\n"
        "I'm your **AI DevOps Assistant**, always ready to help you with **AWS** and **DevOps** tasks!\n\n"
        "👨‍💻 **Builder:** Akhil \n"
        "☁️ **Capabilities:** Manage **EC2**, **S3**, **IAM**, analyze **CloudWatch Logs**, automate with **Terraform**, and more!\n\n"
        "🧠 *Let's simplify cloud management together!*"
    )



# AWS Commands

@tree.command(name="list_ec2", description="List all EC2 instances in your AWS account")
@track_command("list_ec2")
async def list_ec2_cmd(interaction: discord.Interaction):
    await interaction.response.defer()  # shows “thinking…” status
    msg = get_ec2_list()
    await interaction.followup.send(msg[:1990] + "…" if len(msg) > 1990 else msg)


@tree.command(name="list_s3", description="List all S3 buckets")
@track_command("list_s3")
async def list_s3_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    msg = get_s3_list()
    await interaction.followup.send(msg)


@tree.command(name="aws_health", description="Check AWS EC2 and CloudWatch service health")
@track_command("aws_health")
async def aws_health_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    msg = get_health()
    await interaction.followup.send(msg)


@tree.command(name="analyze_logs", description="Summarize CloudWatch log errors and possible fixes")
@track_command("analyze_logs")
@app_commands.describe(
    log_group="Enter your CloudWatch log group name",
    hours="Number of past hours to analyze (default: 1)",
)
async def analyze_logs_cmd(interaction: discord.Interaction, log_group: str, hours: int = 1):
    await interaction.response.defer()
    msg = get_log_analysis(log_group, hours)
    await interaction.followup.send(msg[:1990] + "…" if len(msg) > 1990 else msg)


@tree.command(name="explain", description="Explain any AWS error and suggest a fix")
@track_command("explain")
@app_commands.describe(
    error_message="Paste your AWS error message here"
)
async def explain_cmd(interaction: discord.Interaction, error_message: str):
    await interaction.response.defer()
    answer = explain_error(error_message)
    await interaction.followup.send(answer[:1990] + "…" if len(answer) > 1990 else answer)



@tree.command(name="generate_terraform", description="Create Terraform from plain English")
@track_command("generate_terraform")
@app_commands.describe(description="Type What to build like (VPC, Ec2, Bucket, Lambda, Private subnet, Public subnet, …)")
async def generate_terraform_cmd(interaction: discord.Interaction, description: str):
    await interaction.response.defer()
    code = ai_generate_terraform(description)
    file = discord.File(io.BytesIO(code.encode()), filename="generated.tf")
    await interaction.followup.send("✅ Terraform ready:", file=file)


@tree.command(name="costs", description="AWS spend breakdown (last N days)")
@track_command("costs")
@app_commands.describe(days="Type how many days(default 7)")
async def costs_cmd(interaction: discord.Interaction, days: int = 7):
    await interaction.response.defer()
    try:
        data = get_cost_data(days)
        summary = ai_summarize_cost(days)
        await interaction.followup.send(summary[:1900])
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error fetching AWS cost data: `{e}`")



@tree.command(name="security", description="Quick security posture check")
@track_command("security")
async def security_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    audit = ai_security_audit()
    await interaction.followup.send(audit[:1990])


@tree.command(name="disclaimer", description="Bot limitations and data usage")
async def disclaimer_cmd(interaction: discord.Interaction):
    embed = ai_disclaimer_embed()
    await interaction.response.send_message(embed=embed)




# COMMAND TOGGLE MENU

class FeatureSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Explain AWS Error", description="Explain and fix an AWS error"),
            discord.SelectOption(label="List EC2 Instances", description="Show all running EC2 instances"),
            discord.SelectOption(label="List S3 Buckets", description="Show all available S3 buckets"),
            discord.SelectOption(label="AWS Health", description="Check AWS service status and alarms"),
            discord.SelectOption(label="Analyze Logs", description="Summarize CloudWatch logs and suggest fixes"),
            discord.SelectOption(label="Cost Breakdown", description="Show AWS cost breakdown for the last N days"),
            discord.SelectOption(label="Disclaimer", description="Show bot limitations and data usage"),
            discord.SelectOption(label="Generate Terraform", description="Create Terraform code from plain English"),
            discord.SelectOption(label="Security Audit", description="Check AWS security posture"),
        ]
        super().__init__(placeholder="Choose a DevOps action…", options=options)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        if choice == "Explain AWS Error":
            await interaction.response.send_message("💡 Try `/explain error_message:<your error>`")
        elif choice == "List EC2 Instances":
            await interaction.response.send_message("💻 Use `/list_ec2` to see running instances.")
        elif choice == "List S3 Buckets":
            await interaction.response.send_message("🪣 Use `/list_s3` to view all buckets.")
        elif choice == "AWS Health":
            await interaction.response.send_message("⚙️ Run `/aws_health` to check EC2 & CloudWatch status.")
        elif choice == "Analyze Logs":
            await interaction.response.send_message("📊 Use `/analyze_logs log_group:<name> hours:<1>`.")
        elif choice == "Cost Breakdown":
            await interaction.response.send_message("💰 Try `/costs days:7` for a 7-day cost summary.")
        elif choice == "Disclaimer":
            await interaction.response.send_message("⚠️ Use `/disclaimer` to learn about bot limitations.")
        elif choice == "Generate Terraform":
            await interaction.response.send_message("🛠️ Use `/generate_terraform description:<what you need>`.")
        elif choice == "Security Audit":
            await interaction.response.send_message("🔒 Run `/security` for a quick security posture check.")

class FeatureView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(FeatureSelect())


@tree.command(name="menu", description="Show available DevOps bot features")
async def menu_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🔧 Select a feature from below:", view=FeatureView())



client.run(os.getenv("DISCORD_TOKEN"))
