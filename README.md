# Genshin Auto Daily

Automated daily check-in and code redemption for Genshin Impact using GitHub Actions.

## Features

- Automated daily check-in on HoyoLab
- Auto redeem promotion codes from Genshin Impact Wiki
- Discord webhook notifications (Optional)

## Setup

### 1. Fork this repository

### 2. Configure Secrets

Add the following secrets in Settings > Secrets and variables > Actions:

**Required:**
- `UID` - Genshin Impact player UID
- `REGION` - Server region (`os_usa`, `os_euro`, `os_asia`, `os_cht`) (See [Region Mapping](#region-mapping))
- `COOKIE` - Authentication cookie:
   - Search for how to get cookies from a website
   - You will need to get cookies from the following 2 websites (don't forget to log in):
     - https://www.hoyolab.com/
     - https://genshin.hoyoverse.com/
   - You can take more, but there are 6 required cookies: `ltmid_v2`, `ltuid_v2`, `ltoken_v2`, `account_mid_v2`, `account_id_v2`, `cookie_token_v2`
   - Once you have at least 6 of the above cookies (or all the cookies from 2 websites if you're lazy to filter them out), you need to combine them into a single string, with individual cookies separated by a semicolon and a space [`; `]. For example: `ltuid_v2=sample1; account_id_v2=sample2`
   - **REMEMBER: DONT SHARE YOUR COOKIES WITH ANYONE!!!!**

**Optional:**
- `GIST_ID` - [GitHub Gist](https://gist.github.com/) ID for log storage (you will need to create one, learn how to create a gist and get the gist id)
- `GIST_TOKEN` - Github Personal Access Token (See [docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)): This token requires only a single scope: gist. Avoid selecting multiple scopes to maintain security. You can set the expiration time as needed—just note that once the token expires, you'll have to generate a new one and update the GIST_TOKEN secret accordingly.
- `DISCORD_WEBHOOK_URL` - Discord webhook URL for notifications (If you don't know what this is, see: [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
> If you do not provide the optional secrets, the workflow will still function normally, but related features (such as logging to Gist or sending Discord notifications) will be skipped.

### 3. Enable Actions

Navigate to Actions tab and enable workflows.

## Configuration Details

### Region Mapping
- `os_usa` - America
- `os_euro` - Europe  
- `os_asia` - Asia
- `os_cht` - TW/HK/MO

## Monitoring

- Check workflow status in Actions tab
- View logs for debugging
- Discord notifications (if configured)
- Gist logs (if configured)

## Troubleshooting

- **Actions not running**: Verify workflows are enabled and secrets are configured
- **Check-in failures**: Update expired cookies in secrets
- **Code redemption issues**: Check logs for specific error codes and rate limiting

> Note: Typically, the six cookies used will have a validity of one year. In case of login or authentication errors, you should repeat the cookie retrieval steps and update the secrets with the new values.