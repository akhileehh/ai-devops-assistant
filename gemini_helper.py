import io,discord
import google.generativeai as genai, os
os.environ["GRPC_VERBOSITY"] = "ERROR"
from dotenv import load_dotenv
load_dotenv() 

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def explain_error(error_text: str) -> str:
    prompt = f"Explain this AWS error simply and give one fix:Keep the answer under 1999 characters.\n{error_text}"
    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return response.text.strip()
    except Exception as e:
        return f"Gemini error: {e}"
    


def ai_generate_terraform(description: str) -> str:
    prompt = f"Generate production-ready Terraform (HCL) for AWS:\n- Variables, outputs, encryption, security groups\n- Immediately `terraform validate` ready\nRequest: {description}\nReturn ONLY the .tf code block (no explanations)."
    try:
        rsp = model.generate_content(prompt, generation_config={"temperature": 0.2})
        code = rsp.text.strip()
        if "```" in code:
            code = code.split("```")[1]
            if code.startswith(("hcl", "terraform")):
                code = "\n".join(code.split("\n")[1:])
        return code if code else "# No code returned"
    except Exception as e:
        return f"// There is a error when Generating the code: {e}"


def ai_summarize_cost(days: int) -> str:
    prompt = f"Summarize AWS cost best-practices and typical free-tier spend for {days} days. Keep under 1800 characters."
    try:
        rsp = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return rsp.text.strip()[:1800]
    except Exception as e:
        return f"There is a error while Generating the Cost summary: {e}"
    

def ai_disclaimer_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ DevOps-Bot Disclaimer",
        description=(
            "• Read-only AWS access (no changes)\n"
            "• AI answers may vary—always verify\n"
            "• Logs & errors are **not** stored permanently\n"
            "• Free-tier AWS & Google AI limits apply\n"
            "• Use at your own risk"
        ),
        color=discord.Color.yellow()
    )
    return embed    


def ai_security_audit() -> str:
    prompt = "List top 3 AWS security misconfigurations (root keys, public S3, unencrypted EBS) and one fix each. Keep under 1800 characters."
    try:
        rsp = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return rsp.text.strip()[:1800]
    except Exception as e:
        return f"Security audit error: {e}"
    