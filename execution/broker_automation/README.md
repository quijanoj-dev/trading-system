# Alpha Insider Broker Automation

Connects TradingView strategy alerts → Alpha Insider → broker. No manual execution.

## Setup

### 1. Alpha Insider Account
1. Sign up at alphainsider.com
2. Create a strategy → copy **Strategy ID** and **Webhook URL**
3. Connect your broker (Alpaca, IBKR, Tradovate, etc.)
4. Generate API token under Account Settings

### 2. Configure This Repo
```bash
# Set in shell or .env (never commit the token)
export ALPHA_INSIDER_API_TOKEN=your_token_here
```

Edit `alpha_insider_config.yaml`:
```yaml
strategy_id: "your-strategy-id"
webhook_url: "https://app.alphainsider.com/api/webhook/your-id"
broker:
  name: "alpaca"
  paper_trading: true    # test first!
```

### 3. Test Connection
```bash
python execution/broker_automation/webhook_test.py
```

Prints the TradingView payload template and fires a test ping to Alpha Insider.

### 4. Wire TradingView Alert
In TradingView → Alert → Message, paste:
```json
{
  "action": "{{strategy.order.action}}",
  "contracts": "{{strategy.order.contracts}}",
  "price": "{{close}}",
  "ticker": "{{ticker}}"
}
```

Set Webhook URL = your Alpha Insider webhook URL.

### 5. Go Live
Change `paper_trading: false` in config once paper test passes.

## Flow

```
TradingView strategy fires alert
    → POST JSON to Alpha Insider webhook URL
    → Alpha Insider parses action (buy/sell/close)
    → Alpha Insider routes to connected broker
    → Broker executes order
```

## Environment Variables

| Var | Required | Description |
|-----|----------|-------------|
| `ALPHA_INSIDER_API_TOKEN` | Yes | Auth token from Alpha Insider account settings |

## Dependencies
No new packages needed — uses `requests` (already in requirements.txt).
