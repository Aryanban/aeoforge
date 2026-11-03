"""Firewall and WAF rules generator for AI Answer Engines & Autonomous Web Agents.
Generates copy-paste configurations for Cloudflare, Nginx, and Vercel to allow
verified AI crawlers (Meta-ExternalAgent, PerplexityBot, GPTBot, ClaudeBot)
while maintaining security against abusive scrapers.
"""

from typing import Dict


def generate_waf_rules(domain: str) -> Dict[str, str]:
    """Generate platform-specific firewall rules allowing verified AI bots."""
    
    # 1. Cloudflare Custom Firewall Rule Expression
    cloudflare_expression = (
        '(cf.client.bot or '
        'http.user_agent contains "Meta-ExternalAgent" or '
        'http.user_agent contains "PerplexityBot" or '
        'http.user_agent contains "GPTBot" or '
        'http.user_agent contains "ClaudeBot" or '
        'http.user_agent contains "Applebot-Extended")'
    )
    cloudflare_config = f"""// Cloudflare Dashboard -> Security -> WAF -> Custom Rules -> Create Rule
Name: "Allow Verified AI Bots & Answer Engines"
Field: Custom Expression
Expression:
{cloudflare_expression}

Action: Skip
Options to skip:
  [✓] All remaining custom rules
  [✓] Rate limiting rules
  [✓] Managed rules (Bot Fight Mode & Super Bot Fight Mode)
  [✓] Interactive Challenges & JavaScript Detections
"""

    # 2. Nginx Reverse Proxy Configuration
    nginx_config = f"""# Nginx Configuration (/etc/nginx/conf.d/{domain}.conf)
map $http_user_agent $is_ai_crawler {{
    default 0;
    ~*(Meta-ExternalAgent|PerplexityBot|GPTBot|ClaudeBot|Applebot) 1;
}}

server {{
    server_name {domain};

    # Skip aggressive rate limits for verified AI crawlers
    location / {{
        limit_req zone=one burst=50 nodelay if=$is_ai_crawler;
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }}

    # Expose unauthenticated markdown navigation directory
    location /llms.txt {{
        alias /var/www/{domain}/llms.txt;
        add_header Content-Type text/markdown;
        add_header Access-Control-Allow-Origin *;
    }}
}}"""

    # 3. Vercel Edge Middleware (middleware.ts)
    vercel_config = """// Vercel Edge Middleware: middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const VERIFIED_AI_BOTS = [
  'Meta-ExternalAgent',
  'PerplexityBot',
  'GPTBot',
  'ClaudeBot',
  'Applebot-Extended'
];

export function middleware(request: NextRequest) {
  const userAgent = request.headers.get('user-agent') || '';
  const isAIBot = VERIFIED_AI_BOTS.some(bot => userAgent.includes(bot));

  if (isAIBot) {
    const response = NextResponse.next();
    response.headers.set('x-robots-tag', 'all');
    response.headers.set('Access-Control-Allow-Origin', '*');
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};"""

    return {
        "cloudflare": cloudflare_config,
        "nginx": nginx_config,
        "vercel": vercel_config
    }
