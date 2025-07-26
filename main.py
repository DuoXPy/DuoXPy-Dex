#!/usr/bin/env python3
"""
DuoXPy Dex CLI
A standalone tool to create Duolingo accounts using the same methods as DuoXPy
"""

import json
import base64
import uuid
import aiohttp
import time
import datetime
import asyncio
import re
import secrets
import string
import os
import random
import pytz
import threading
from urllib.parse import quote
from aiohttp_socks import ProxyConnector, ProxyConnectionError
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich import box
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

# Initialize Rich console
console = Console()

# Load environment variables
load_dotenv()

# Constants
NAME = "www․DuoXPy․site"

# Account status tracking
class AccountStatus:
    PENDING = "pending"
    CREATING = "creating"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    RATE_LIMITED = "rate_limited"

class AccountProgress:
    def __init__(self, account_id: int):
        self.account_id = account_id
        self.status = AccountStatus.PENDING
        self.progress = 0
        self.message = "Waiting to start..."
        self.start_time = None
        self.end_time = None
        self.retry_count = 0
        self.rate_limit_until = None
        self.account_data = None
        self.error_message = None
        self.proxy_used = "Direct"
        self.connection_type = "Direct"
        self.fallback_count = 0

def load_proxies():
    """Load proxies from proxies.txt file"""
    proxies = []
    try:
        if os.path.exists("proxies.txt"):
            with open("proxies.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)
    except Exception as e:
        console.print(f"[red]Error loading proxies: {e}[/red]")
    return proxies

def print_banner():
    """Print a beautiful banner with Rich"""
    banner_text = Text()
    banner_text.append("🚀 ", style="bold magenta")
    banner_text.append("DuoXPy Dex CLI", style="bold cyan")
    banner_text.append(" 🚀", style="bold magenta")
    
    subtitle = Text("Create Duolingo accounts with style and ease!", style="green")
    
    panel = Panel(
        Align.center(banner_text),
        subtitle=subtitle,
        border_style="magenta",
        box=box.DOUBLE
    )
    console.print(panel)

def print_proxy_info(proxies):
    """Print proxy information"""
    if proxies:
        proxy_text = Text()
        proxy_text.append("🔗 ", style="bold green")
        proxy_text.append(f"Loaded {len(proxies)} proxy(ies) from proxies.txt", style="green")
        proxy_text.append(" 🔗", style="bold green")
        
        panel = Panel(
            proxy_text,
            border_style="green",
            box=box.ROUNDED
        )
        console.print(panel)
    else:
        proxy_text = Text()
        proxy_text.append("🌐 ", style="bold yellow")
        proxy_text.append("No proxies found - using direct connection (make proxies.txt for proxies)", style="yellow")
        proxy_text.append(" 🌐", style="bold yellow")
        
        panel = Panel(
            proxy_text,
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(panel)

def create_progress_table(accounts_progress: List[AccountProgress], total_accounts: int):
    """Create a beautiful Rich table for progress tracking"""
    # Calculate overall progress
    completed = sum(1 for acc in accounts_progress if acc.status == AccountStatus.SUCCESS)
    failed = sum(1 for acc in accounts_progress if acc.status == AccountStatus.FAILED)
    in_progress = sum(1 for acc in accounts_progress if acc.status in [AccountStatus.CREATING, AccountStatus.RETRYING])
    pending = total_accounts - completed - failed - in_progress
    
    # Create table with very compact columns
    table = Table(title=f"Account Creation Progress ({total_accounts} accounts)", box=box.SIMPLE)
    table.add_column("ID", style="cyan", justify="center", width=2)
    table.add_column("Status", style="magenta", justify="center", width=8)
    table.add_column("Progress", style="blue", justify="center", width=12)
    table.add_column("Conn", style="yellow", justify="center", width=6)
    table.add_column("Proxy", style="green", justify="center", width=8)
    table.add_column("Time", style="yellow", justify="center", width=6)
    table.add_column("Message", style="white", justify="left", width=20)
    
    # Add rows for all accounts
    for acc in accounts_progress:
        # Status emoji and color
        if acc.status == AccountStatus.SUCCESS:
            status_emoji = "✅"
            status_style = "bold green"
        elif acc.status == AccountStatus.FAILED:
            status_emoji = "❌"
            status_style = "bold red"
        elif acc.status == AccountStatus.RETRYING:
            status_emoji = "🔄"
            status_style = "bold yellow"
        elif acc.status == AccountStatus.RATE_LIMITED:
            status_emoji = "⏱️"
            status_style = "bold red"
        elif acc.status == AccountStatus.CREATING:
            status_emoji = "🔄"
            status_style = "bold blue"
        else:
            status_emoji = "⏳"
            status_style = "gray"
        
        # Progress bar (very short)
        progress_bar_length = 6
        filled_progress = int(progress_bar_length * acc.progress // 100)
        progress_bar = "█" * filled_progress + "░" * (progress_bar_length - filled_progress)
        
        # Connection type with emoji
        if acc.connection_type == "Proxy":
            connection_emoji = "🔗"
        else:
            connection_emoji = "🌐"
        
        # Proxy info (very short)
        proxy_display = acc.proxy_used[:6] + ".." if len(acc.proxy_used) > 6 else acc.proxy_used
        
        # Time elapsed
        if acc.start_time:
            if acc.end_time:
                elapsed = acc.end_time - acc.start_time
            else:
                elapsed = datetime.datetime.now() - acc.start_time
            time_str = f"{elapsed.total_seconds():.0f}s"
        else:
            time_str = "0s"
        
        # Message (very short)
        message = acc.message[:18] + ".." if len(acc.message) > 18 else acc.message
        
        table.add_row(
            str(acc.account_id),
            f"{status_emoji} {acc.status[:6]}",
            f"[{progress_bar}] {acc.progress}%",
            f"{connection_emoji} {acc.connection_type[:3]}",
            proxy_display,
            time_str,
            message
        )
    
    return table, completed, failed, in_progress, pending

def create_overall_progress(completed, failed, in_progress, pending, total):
    """Create overall progress display"""
    overall_progress = (completed + failed) / total * 100
    
    progress_text = Text()
    progress_text.append("📊 Overall Progress: ", style="bold blue")
    progress_text.append(f"{overall_progress:.1f}%", style="bold green")
    
    stats_text = Text()
    stats_text.append("✅ Completed: ", style="bold green")
    stats_text.append(f"{completed}", style="green")
    stats_text.append(" | ❌ Failed: ", style="bold red")
    stats_text.append(f"{failed}", style="red")
    stats_text.append(" | 🔄 In Progress: ", style="bold yellow")
    stats_text.append(f"{in_progress}", style="yellow")
    stats_text.append(" | ⏳ Pending: ", style="bold cyan")
    stats_text.append(f"{pending}", style="cyan")
    
    return progress_text, stats_text

def create_account_summary(accounts_progress: List[AccountProgress], total_accounts: int):
    """Create a compact summary of all accounts"""
    # Group accounts by status
    completed = [acc for acc in accounts_progress if acc.status == AccountStatus.SUCCESS]
    failed = [acc for acc in accounts_progress if acc.status == AccountStatus.FAILED]
    in_progress = [acc for acc in accounts_progress if acc.status in [AccountStatus.CREATING, AccountStatus.RETRYING]]
    pending = [acc for acc in accounts_progress if acc.status == AccountStatus.PENDING]
    rate_limited = [acc for acc in accounts_progress if acc.status == AccountStatus.RATE_LIMITED]
    
    summary_text = Text()
    summary_text.append("📋 Account Summary: ", style="bold purple")
    
    if completed:
        summary_text.append(f"✅ {len(completed)} completed", style="green")
        summary_text.append(" | ", style="white")
    
    if in_progress:
        summary_text.append(f"🔄 {len(in_progress)} in progress", style="yellow")
        summary_text.append(" | ", style="white")
    
    if rate_limited:
        summary_text.append(f"⏱️ {len(rate_limited)} rate limited", style="red")
        summary_text.append(" | ", style="white")
    
    if failed:
        summary_text.append(f"❌ {len(failed)} failed", style="red")
        summary_text.append(" | ", style="white")
    
    if pending:
        summary_text.append(f"⏳ {len(pending)} pending", style="cyan")
    
    return summary_text

class TempMail:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.tempmail.lol"

    async def create_inbox(self, domain=None, prefix=None):
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "apikey": self.api_key,
            "domain": domain,
            "prefix": prefix
        }
        
        async with await get_session(direct=True) as session:
            async with session.post(f"{self.base_url}/v2/inbox/create", headers=headers, json=data) as response:
                response.raise_for_status()
                try:
                    return await response.json()
                except ValueError:
                    if response.headers.get("Content-Type") == "text/html":
                        console.print(f"[red]HTML response received: {await response.text()}[/red]")
                    else:
                        console.print(f"[red]Invalid JSON response: {await response.text()}[/red]")
                    raise Exception("Invalid JSON response from TempMail API")

    async def get_emails(self, inbox):
        params = {
            "apikey": self.api_key,
            "token": inbox["token"]
        }
        
        async with await get_session(direct=True) as session:
            async with session.get(f"{self.base_url}/v2/inbox", params=params) as response:
                response.raise_for_status()
                try:
                    data = await response.json()
                    emails = data["emails"]
                    return emails
                except ValueError:
                    if response.headers.get("Content-Type") == "text/html":
                        console.print(f"[red]HTML response received: {await response.text()}[/red]")
                    else:
                        console.print(f"[red]Invalid JSON response: {await response.text()}[/red]")
                    raise Exception("Invalid JSON response from TempMail API")

class Miscellaneous:
    def randomize_mobile_user_agent(self) -> str:
        duolingo_version = "6.26.2"
        android_version = random.randint(12, 15)
        build_codes = ['AE3A', 'TQ3A', 'TP1A', 'SP2A', 'UP1A', 'RQ3A', 'RD2A', 'SD2A']
        build_date = f"{random.randint(220101, 240806)}"
        build_suffix = f"{random.randint(1, 999):03d}"
        
        devices = [
            'sdk_gphone64_x86_64',
            'Pixel 6',
            'Pixel 6 Pro',
            'Pixel 7',
            'Pixel 7 Pro', 
            'Pixel 8',
            'SM-A536B',
            'SM-S918B',
            'SM-G998B',
            'SM-N986B',
            'OnePlus 9 Pro',
            'OnePlus 10 Pro',
            'M2102J20SG',
            'M2012K11AG'
        ]
        
        device = random.choice(devices)
        build_code = random.choice(build_codes)
        
        user_agent = f"Duodroid/{duolingo_version} Dalvik/2.1.0 (Linux; U; Android {android_version}; {device} Build/{build_code}.{build_date}.{build_suffix})"
        return user_agent

    def randomize_computer_user_agent(self) -> str:
        platforms = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 10.0; WOW64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "Macintosh; Intel Mac OS X 11_2_3",
            "X11; Linux x86_64",
            "X11; Linux i686",
            "X11; Ubuntu; Linux x86_64",
        ]
        
        browsers = [
            ("Chrome", f"{random.randint(90, 140)}.0.{random.randint(1000, 4999)}.0"),
            ("Firefox", f"{random.randint(80, 115)}.0"),
            ("Safari", f"{random.randint(13, 16)}.{random.randint(0, 3)}"),
            ("Edge", f"{random.randint(90, 140)}.0.{random.randint(1000, 4999)}.0"),
        ]
        
        webkit_version = f"{random.randint(500, 600)}.{random.randint(0, 99)}"
        platform = random.choice(platforms)
        browser_name, browser_version = random.choice(browsers)
        
        if browser_name == "Safari":
            user_agent = (
                f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit_version} (KHTML, like Gecko) "
                f"Version/{browser_version} Safari/{webkit_version}"
            )
        elif browser_name == "Firefox":
            user_agent = f"Mozilla/5.0 ({platform}; rv:{browser_version}) Gecko/20100101 Firefox/{browser_version}"
        else:
            user_agent = (
                f"Mozilla/5.0 ({platform}) AppleWebKit/{webkit_version} (KHTML, like Gecko) "
                f"{browser_name}/{browser_version} Safari/{webkit_version}"
            )
        
        return user_agent

async def get_session(slot: Optional[int] = None, direct: bool = False, proxies: List[str] = None, progress: AccountProgress = None):
    if direct:
        # Create SSL context that ignores certificate verification
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(force_close=True, ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=600, connect=600, sock_read=600, sock_connect=600)
        return aiohttp.ClientSession(connector=connector, timeout=timeout)

    # Use proxy if available and account is marked for proxy use
    if proxies and slot is not None and progress and progress.connection_type == "Proxy":
        # Try proxies in rotation order
        proxy_index = slot % len(proxies)
        proxy = proxies[proxy_index]
        
        try:
            connector = ProxyConnector.from_url(proxy, force_close=True)
            timeout = aiohttp.ClientTimeout(total=600, connect=600, sock_read=600, sock_connect=600)
            session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            
            # Test the proxy with a quick request
            try:
                async with session.get("https://www.duolingo.com", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        if progress:
                            progress.proxy_used = f"Proxy {proxy_index + 1}"
                            progress.connection_type = "Proxy"
                        return session
            except Exception as e:
                await session.close()
                raise e
                
        except Exception as e:
            if progress:
                progress.fallback_count += 1
                progress.message = f"Proxy {proxy_index + 1} failed, trying direct..."
            await session.close()
    
    # Fallback to direct connection
    if progress:
        progress.proxy_used = "Direct"
        progress.connection_type = "Direct"
        if progress.fallback_count > 0:
            progress.message = f"Using direct connection (proxy failed)"
    
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(force_close=True, ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=600, connect=600, sock_read=600, sock_connect=600)
    return aiohttp.ClientSession(connector=connector, timeout=timeout)

async def getheaders(token: str, userid: str):
    misc = Miscellaneous()
    user_agent = misc.randomize_mobile_user_agent()
    
    headers = {
        "accept": "application/json", 
        "authorization": f"Bearer {token}",
        "connection": "Keep-Alive",
        "content-type": "application/json",
        "cookie": f"jwt_token={token}",
        "origin": "https://www.duolingo.com",
        "user-agent": user_agent,
        "x-amzn-trace-id": f"User={userid}",
    }
    return headers

def generate_random_password(length: int = 12) -> str:
    """Generate a random password with letters, numbers, and symbols"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

class DuolingoAccountCreator:
    def __init__(self, proxies: List[str] = None):
        self.misc = Miscellaneous()
        self.tmp = TempMail(os.getenv('TEMPMAIL_API_KEY'))
        self.proxies = proxies or []

    def generate_random_string(self, min_length: int = 4, max_length: int = 16) -> str:
        length = random.randint(min_length, max_length)
        valid_chars = string.ascii_letters + string.digits + "-._"
        username = random.choice(string.ascii_letters)
        username += ''.join(random.choices(valid_chars, k=length-1))
        return username

    async def create_account_with_progress(self, password: str, progress: AccountProgress) -> dict:
        try:
            progress.start_time = datetime.datetime.now()
            progress.status = AccountStatus.CREATING
            progress.progress = 5
            progress.message = "Creating unclaimed account..."
            
            headers = {
                'accept': 'application/json', 
                'connection': 'Keep-Alive',
                'content-type': 'application/json',
                'host': 'android-api-cf.duolingo.com',
                'user-agent': self.misc.randomize_mobile_user_agent(),
                'x-amzn-trace-id': 'User=0'
            }

            params = {
                'fields': 'id,creationDate,fromLanguage,courses,currentCourseId,username,health,zhTw,hasPlus,joinedClassroomIds,observedClassroomIds,roles'
            }

            json_data = {
                'currentCourseId': 'DUOLINGO_FR_EN',
                'distinctId': str(uuid.uuid4()),
                'fromLanguage': 'en',
                'timezone': 'Asia/Saigon',
                'zhTw': False
            }

            # Use proxy if available with intelligent distribution
            proxy_slot = progress.account_id - 1 if self.proxies else None
            # Only use proxy if account is marked for proxy use
            use_proxy = bool(self.proxies) and progress.connection_type == "Proxy"
            async with await get_session(slot=proxy_slot, direct=not use_proxy, proxies=self.proxies, progress=progress) as session:
                # Retry logic for creating unclaimed account with proxy fallback
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with session.post(
                            'https://android-api-cf.duolingo.com/2023-05-23/users',
                            params=params,
                            headers=headers,
                            json=json_data
                        ) as response:
                            if response.status == 429:  # Rate limited
                                progress.status = AccountStatus.RATE_LIMITED
                                progress.message = f"Rate limited on {progress.connection_type}, retrying..."
                                await asyncio.sleep(5)
                                continue
                            elif response.status != 200:
                                if attempt < max_retries - 1:
                                    progress.status = AccountStatus.RETRYING
                                    progress.message = f"Retrying unclaimed account creation... (Attempt {attempt + 1})"
                                    await asyncio.sleep(2)
                                    continue
                                else:
                                    raise Exception("Failed to create unclaimed account")
                            data = await response.json()
                            duo_id = data.get("id")
                            jwt = response.headers.get("Jwt")
                            if not duo_id or not jwt:
                                raise Exception("Failed to get duo_id or jwt")
                            progress.progress = 15
                            progress.message = f"Unclaimed account created - ID: {duo_id}"
                            break
                    except Exception as e:
                        if "rate limit" in str(e).lower() or "429" in str(e):
                            progress.status = AccountStatus.RATE_LIMITED
                            progress.message = f"Rate limited, switching connection..."
                            await asyncio.sleep(5)
                            # Try to switch proxy or go direct
                            if self.proxies and progress.connection_type == "Proxy":
                                progress.fallback_count += 1
                                progress.message = "Switching to direct connection..."
                                # Create new session with direct connection
                                await session.close()
                                session = await get_session(direct=True, progress=progress)
                            continue
                        elif attempt < max_retries - 1:
                            progress.status = AccountStatus.RETRYING
                            progress.message = f"Retrying... (Attempt {attempt + 1})"
                            await asyncio.sleep(2)
                            continue
                        else:
                            raise e

                await asyncio.sleep(2)
                progress.progress = 25
                progress.message = "Creating email inbox..."
                username = self.generate_random_string()
                inbox = await self.tmp.create_inbox(None, username)
                if not inbox:
                    raise Exception("Failed to create email inbox")
                email = inbox["address"]
                progress.progress = 35
                progress.message = f"Email inbox created - {email}"

                progress.progress = 45
                progress.message = "Claiming account..."
                headers = await getheaders(jwt, duo_id)
                json_data = {
                    'requests': [{
                        'body': json.dumps({
                            'age': str(random.randint(18, 50)),
                            'distinctId': f"UserId(id={duo_id})",
                            'email': email,
                            'emailPromotion': True,
                            'name': NAME,
                            'firstName': NAME,
                            'lastName': NAME,
                            'username': username,
                            'password': password,
                            'pushPromotion': True,
                            'timezone': 'Asia/Saigon'
                        }),
                        'bodyContentType': 'application/json',
                        'method': 'PATCH',
                        'url': f'/2023-05-23/users/{duo_id}?fields=id,email,name'
                    }]
                }

                async with session.post(
                    'https://android-api-cf.duolingo.com/2017-06-30/batch',
                    params={'fields': 'responses'},
                    headers=headers,
                    json=json_data
                ) as response:
                    if response.status != 200:
                        raise Exception("Failed to claim account")
                progress.progress = 55
                progress.message = "Account claimed successfully"

                await asyncio.sleep(2)
                progress.progress = 65
                progress.message = "Completing initial lesson..."
                session_data = None
                base_url = "https://www.duolingo.com"
                lesson_headers = {
                    "Authorization": f"Bearer {jwt}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "Accept": "application/json; charset=UTF-8",
                    "User-Agent": self.misc.randomize_computer_user_agent(),
                    "Origin": "https://www.duolingo.com",
                    "Referer": "https://www.duolingo.com/lesson"
                }
                url = f"{base_url}/2017-06-30/sessions"
                payload = {
                    "challengeTypes": [
                        "assist", "characterIntro", "characterMatch", "characterPuzzle",
                        "characterSelect", "characterTrace", "characterWrite",
                        "completeReverseTranslation", "definition", "dialogue",
                        "extendedMatch", "extendedListenMatch", "form", "freeResponse",
                        "gapFill", "judge", "listen", "listenComplete", "listenMatch",
                        "match", "name", "listenComprehension", "listenIsolation",
                        "listenSpeak", "listenTap", "orderTapComplete", "partialListen",
                        "partialReverseTranslate", "patternTapComplete", "radioBinary",
                        "radioImageSelect", "radioListenMatch", "radioListenRecognize",
                        "radioSelect", "readComprehension", "reverseAssist", "sameDifferent",
                        "select", "selectPronunciation", "selectTranscription", "svgPuzzle",
                        "syllableTap", "syllableListenTap", "speak", "tapCloze",
                        "tapClozeTable", "tapComplete", "tapCompleteTable", "tapDescribe",
                        "translate", "transliterate", "transliterationAssist", "typeCloze",
                        "typeClozeTable", "typeComplete", "typeCompleteTable", "writeComprehension"
                    ],
                    "fromLanguage": "en",
                    "isFinalLevel": False,
                    "isV2": True,
                    "juicy": True,
                    "learningLanguage": "fr",
                    "shakeToReportEnabled": True,
                    "smartTipsVersion": 2,
                    "isCustomIntroSkill": False,
                    "isGrammarSkill": False,
                    "levelIndex": 0,
                    "pathExperiments": [],
                    "showGrammarSkillSplash": False,
                    "skillId": "fc5f14f4f4d2451e18f3f03725a5d5b1",
                    "type": "LESSON",
                    "levelSessionIndex": 0
                }

                async with session.post(url, json=payload, headers=lesson_headers) as response:
                    if response.status == 200:
                        session_data = await response.json()
                        session_id = session_data.get("id")
                        await asyncio.sleep(2)
                        url = f"{base_url}/2017-06-30/sessions/{session_id}"
                        complete_headers = lesson_headers.copy()
                        complete_headers["Idempotency-Key"] = session_id
                        complete_headers["X-Requested-With"] = "XMLHttpRequest"
                        complete_headers["User"] = str(duo_id)
                        session_data["failed"] = False
                        current_time = datetime.datetime.now(pytz.timezone("Asia/Saigon"))
                        elapsed_time = 45 + (current_time.timestamp() % 15)
                        session_data["trackingProperties"]["sum_time_taken"] = elapsed_time
                        session_data["xpGain"] = 15
                        session_data["trackingProperties"]["xp_gained"] = 15

                        activity_uuid = session_data.get("trackingProperties", {}).get("activity_uuid")
                        if not activity_uuid:
                            activity_uuid = str(uuid.uuid4())
                            session_data["trackingProperties"]["activity_uuid"] = activity_uuid

                        await session.put(url, json=session_data, headers=complete_headers)
                        await asyncio.sleep(2)
                        progress.progress = 75
                        progress.message = "Initial lesson completed"
                    else:
                        raise Exception(f"Failed to complete lesson. Status: {response.status}")

                progress.progress = 85
                progress.message = "Farming XP from stories..."
                for i in range(10):
                    current_time = datetime.datetime.now(pytz.timezone("Asia/Saigon"))
                    url = f'https://stories.duolingo.com/api2/stories/fr-en-le-passeport/complete'
                    dataget = {
                        "awardXp": True,
                        "completedBonusChallenge": True,
                        "fromLanguage": "en",
                        "hasXpBoost": False,
                        "illustrationFormat": "svg",
                        "isFeaturedStoryInPracticeHub": True,
                        "isLegendaryMode": True,
                        "isV2Redo": False,
                        "isV2Story": False,
                        "learningLanguage": "fr",
                        "masterVersion": True,
                        "maxScore": 0,
                        "score": 0,
                        "happyHourBonusXp": random.randint(0, 465),
                        "startTime": current_time.timestamp(),
                        "endTime": datetime.datetime.now(pytz.timezone("Asia/Saigon")).timestamp(),
                    }
                    retry_count = 0
                    while True:
                        async with session.post(url=url, headers=headers, json=dataget) as response:
                            if response.status == 200:
                                await asyncio.sleep(2)
                                break
                            else:
                                retry_count += 1
                                if retry_count < 10:
                                    await asyncio.sleep(60)
                                else:
                                    raise Exception(f"Failed to farm XP after 10 attempts. Status: {response.status}")
                progress.progress = 100
                progress.message = "XP farming completed"
                        
                account_data = {
                    "_id": duo_id,
                    "email": email,
                    "password": password,
                    "jwt_token": jwt,
                    "timezone": "Asia/Saigon", 
                    "username": username
                }

                progress.end_time = datetime.datetime.now()
                progress.status = AccountStatus.SUCCESS
                progress.message = "Account created successfully!"
                progress.account_data = account_data

            return account_data
        except Exception as e:
            progress.end_time = datetime.datetime.now()
            progress.status = AccountStatus.FAILED
            progress.message = f"Failed: {str(e)}"
            progress.error_message = str(e)
            raise Exception(f"Failed to create account: {str(e)}")

    async def create_account(self, password: str) -> dict:
        """Create a single account (for single-threaded mode)"""
        # Create a temporary progress object for single-threaded mode
        temp_progress = AccountProgress(1)
        return await self.create_account_with_progress(password, temp_progress)

def save_accounts_to_file(accounts: List[Dict], filename: str = "accounts.json", file_format: str = "json"):
    """Save accounts to a file in the specified format"""
    try:
        if file_format.lower() == "txt":
            # Save as TXT format: user:password:email
            with open(filename, 'w') as f:
                for account in accounts:
                    f.write(f"{account['username']}:{account['password']}:{account['email']}\n")
            console.print(f"[green]✅ Accounts saved to {filename} (TXT format)[/green]")
        else:
            # Save as JSON format
            with open(filename, 'w') as f:
                json.dump(accounts, f, indent=2)
            console.print(f"[green]✅ Accounts saved to {filename} (JSON format)[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error saving accounts: {e}[/red]")

def get_user_input():
    """Get user input for account creation settings"""
    print_banner()
    
    # Load and display proxy info
    proxies = load_proxies()
    print_proxy_info(proxies)
    
    console.print("\n[bold magenta]⚙️ Configuration Setup[/bold magenta]")
    console.print("─" * 80)
    
    # Get number of accounts
    while True:
        try:
            count_input = Prompt.ask(
                "[cyan]📊 How many accounts do you want to create?[/cyan]",
                default="1"
            )
            count = int(count_input)
            if 1 <= count <= 100:
                break
            else:
                console.print("[red]❌ Please enter a number between 1 and 100.[/red]")
        except ValueError:
            console.print("[red]❌ Please enter a valid number.[/red]")
    
    # Ask for multi-threading if more than 1 account
    use_multithreading = False
    if count > 1:
        console.print("\n[bold purple]🧵 Multi-Threading Option[/bold purple]")
        console.print("[green]⚡ Multi-threading will create accounts simultaneously for faster creation![/green]")
        console.print("[yellow]⚠️ Note: This may trigger rate limits more easily[/yellow]")
        
        use_multithreading = Confirm.ask("[cyan]🧵 Use multi-threading?[/cyan]", default=True)
    
    # Get delay between accounts (only for single-threaded)
    delay = 0
    if not use_multithreading:
        while True:
            try:
                delay_input = Prompt.ask(
                    "[cyan]⏰ Delay between accounts in seconds?[/cyan]",
                    default="0"
                )
                delay = int(delay_input)
                if 0 <= delay <= 300:
                    break
                else:
                    console.print("[red]❌ Please enter a number between 0 and 300.[/red]")
            except ValueError:
                console.print("[red]❌ Please enter a valid number.[/red]")
    
    # Get output filename
    filename = Prompt.ask(
        "[cyan]💾 Output filename?[/cyan]",
        default="accounts.json"
    )
    if not filename.endswith('.json') and not filename.endswith('.txt'):
        filename += '.json'
    
    # Get file format
    console.print("\n[bold purple]📄 File Format Selection[/bold purple]")
    console.print("[cyan]1. JSON format (default) - Full account data with all details[/cyan]")
    console.print("[cyan]2. TXT format - Simple user:password:email format[/cyan]")
    
    while True:
        try:
            format_choice = Prompt.ask(
                "[cyan]📄 Select file format (1/2)[/cyan]",
                default="1"
            )
            if format_choice in ["1", "2"]:
                file_format = "json" if format_choice == "1" else "txt"
                # Update filename extension if needed
                if file_format == "txt" and filename.endswith('.json'):
                    filename = filename[:-5] + '.txt'
                elif file_format == "json" and filename.endswith('.txt'):
                    filename = filename[:-4] + '.json'
                break
            else:
                console.print("[red]❌ Please enter 1 or 2.[/red]")
        except ValueError:
            console.print("[red]❌ Please enter a valid choice.[/red]")
    
    return count, delay, filename, use_multithreading, proxies, file_format

async def create_accounts_multithreaded(count: int, filename: str, proxies: List[str], file_format: str):
    """Create accounts using multi-threading with Rich progress table and intelligent proxy distribution"""
    creator = DuolingoAccountCreator(proxies)
    accounts_progress = [AccountProgress(i+1) for i in range(count)]
    successful_accounts = []
    
    # Intelligent distribution: some accounts use proxies, some use direct
    if proxies:
        # Distribute accounts: 70% use proxies, 30% use direct
        proxy_accounts = int(count * 0.7)
        direct_accounts = count - proxy_accounts
        
        console.print(f"[green]🔗 {proxy_accounts} accounts will use proxies[/green]")
        console.print(f"[yellow]🌐 {direct_accounts} accounts will use direct connection[/yellow]")
        
        # Mark which accounts should use direct connection
        for i in range(proxy_accounts, count):
            accounts_progress[i].connection_type = "Direct"
            accounts_progress[i].proxy_used = "Direct"
    
    # Create tasks for all accounts
    tasks = []
    for i in range(count):
        password = generate_random_password()
        task = asyncio.create_task(creator.create_account_with_progress(password, accounts_progress[i]))
        tasks.append(task)
    
    # Start progress monitoring with Rich Live
    with Live(console=console, refresh_per_second=2) as live:
        while not all(task.done() for task in tasks):
            table, completed, failed, in_progress, pending = create_progress_table(accounts_progress, count)
            progress_text, stats_text = create_overall_progress(completed, failed, in_progress, pending, count)
            summary_text = create_account_summary(accounts_progress, count)
            
            # Create compact layout
            layout = Layout()
            layout.split_column(
                Layout(Panel(progress_text, border_style="blue", padding=(0, 1))),
                Layout(Panel(stats_text, border_style="cyan", padding=(0, 1))),
                Layout(Panel(summary_text, border_style="purple", padding=(0, 1))),
                Layout(table)
            )
            
            live.update(layout)
            await asyncio.sleep(0.5)
    
    # Wait for all accounts to complete
    for task in asyncio.as_completed(tasks):
        try:
            account_data = await task
            successful_accounts.append(account_data)
        except Exception as e:
            pass  # Error already handled in progress tracking
    
    # Final progress display
    table, completed, failed, in_progress, pending = create_progress_table(accounts_progress, count)
    progress_text, stats_text = create_overall_progress(completed, failed, in_progress, pending, count)
    summary_text = create_account_summary(accounts_progress, count)
    
    # Create compact layout
    layout = Layout()
    layout.split_column(
        Layout(Panel(progress_text, border_style="blue", padding=(0, 1))),
        Layout(Panel(stats_text, border_style="cyan", padding=(0, 1))),
        Layout(Panel(summary_text, border_style="purple", padding=(0, 1))),
        Layout(table)
    )
    
    console.print(layout)
    
    # Save successful accounts
    if successful_accounts:
        save_accounts_to_file(successful_accounts, filename, file_format)
    
    return successful_accounts

async def create_accounts_single_threaded(count: int, delay: int, filename: str, proxies: List[str], file_format: str):
    """Create accounts using single-threaded approach with Rich progress"""
    creator = DuolingoAccountCreator(proxies)
    accounts = []
    
    console.print("\n[bold purple]⭐ Starting Account Creation ⭐[/bold purple]")
    console.print("─" * 80)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        for i in range(count):
            task = progress.add_task(f"[cyan]Creating Account {i+1}/{count}[/cyan]", total=100)
            
            try:
                # Generate random password and username
                password = generate_random_password()
                console.print(f"[green]🔒 Generated password: {password}[/green]")
                
                account = await creator.create_account(password)
                accounts.append(account)
                progress.update(task, completed=100)
                
                console.print(f"[green]✅ Account {i+1} created successfully![/green]")
                
                # Beautiful account info display
                console.print(f"[cyan]📧 Email: {account['email']}[/cyan]")
                console.print(f"[purple]👤 Username: {account['username']}[/purple]")
                console.print(f"[green]🔒 Password: {account['password']}[/green]")
                console.print(f"[yellow]🆔 Duo ID: {account['_id']}[/yellow]")
                
                # Save after each successful creation
                save_accounts_to_file(accounts, filename, file_format)
                
                # Delay before next account (except for the last one)
                if i < count - 1 and delay > 0:
                    console.print(f"[blue]⏳ Waiting {delay} seconds before next account...[/blue]")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                console.print(f"[red]❌ Failed to create account {i+1}: {e}[/red]")
                continue
    
    return accounts

async def main():
    # Check for required environment variable
    if not os.getenv('TEMPMAIL_API_KEY'):
        print_banner()
        console.print("[red]❌ TEMPMAIL_API_KEY environment variable is required[/red]")
        console.print("[cyan]ℹ️ Please set it in your .env file or environment[/cyan]")
        console.print("[cyan]ℹ️ Get your API key from: https://tempmail.lol/[/cyan]")
        input("Press Enter to exit...")
        return
    
    # Get user input
    count, delay, filename, use_multithreading, proxies, file_format = get_user_input()
    
    console.print("\n[bold purple]⭐ Account Creation Settings ⭐[/bold purple]")
    console.print("─" * 80)
    console.print(f"[green]📊 Number of accounts: {count}[/green]")
    if use_multithreading:
        console.print(f"[green]🧵 Multi-threading: Enabled[/green]")
    else:
        console.print(f"[yellow]⏰ Delay between accounts: {delay} seconds[/yellow]")
    console.print(f"[cyan]💾 Output file: {filename}[/cyan]")
    console.print(f"[purple]📄 File format: {file_format.upper()}[/purple]")
    if proxies:
        console.print(f"[green]🔗 Proxies: {len(proxies)} loaded[/green]")
    console.print("─" * 80)
    
    # Confirm before starting
    if not Confirm.ask("[cyan]🚀 Ready to start creating accounts?[/cyan]", default=True):
        console.print("[yellow]⚠️ Account creation cancelled.[/yellow]")
        return
    
    # Create accounts based on threading preference
    if use_multithreading:
        accounts = await create_accounts_multithreaded(count, filename, proxies, file_format)
    else:
        accounts = await create_accounts_single_threaded(count, delay, filename, proxies, file_format)
    
    console.print("\n[bold purple]⭐ Account Creation Completed ⭐[/bold purple]")
    console.print("─" * 80)
    console.print(f"[green]✅ Successfully created: {len(accounts)}/{count} accounts[/green]")
    console.print(f"[cyan]💾 All accounts saved to: {filename}[/cyan]")
    
    if accounts:
        console.print("\n[bold purple]⭐ Account Summary ⭐[/bold purple]")
        console.print("─" * 80)
        
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("#", style="cyan", justify="center")
        summary_table.add_column("Username", style="purple")
        summary_table.add_column("Email", style="cyan")
        summary_table.add_column("Password", style="green")
        
        for i, account in enumerate(accounts, 1):
            summary_table.add_row(
                str(i),
                account['username'],
                account['email'],
                account['password']
            )
        
        console.print(summary_table)
    
    console.print("─" * 80)
    console.print("[bold purple]💚 Thank you for using DuoXPy Dex! 💚[/bold purple]")
    input("Press Enter to exit...")

if __name__ == "__main__":
    asyncio.run(main()) 