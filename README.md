# Genshin Auto Daily

Template repository for automated daily check-in and code redemption for Genshin Impact using GitHub Actions.

## Features

- Automated daily check-in on HoyoLab
- Auto redeem promotion codes from [Genshin Impact Wiki](https://genshin-impact.fandom.com/wiki/Promotional_Code)
- Discord webhook notifications (Optional)
- Ready-to-use GitHub Actions workflows

## Setup

### 1. Use this template

Create your own repository from this template:
- Click the "Use this template" button
- Select "Create a new repository"
- Enter your desired repository name
- Click "Create repository" to finish
- You will be redirected to your new repository

### 2. Configure Secrets
> Read [GitHub Secrets Docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) if you don't know how to do this.

Add the following secrets in Settings > Secrets and variables > Actions > New repository secret:

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
   - Set the combined cookie string as the value for the `COOKIE` secret.
   - **REMEMBER: DONT SHARE YOUR COOKIES WITH ANYONE!!!!**

**Optional:**
- `DISCORD_WEBHOOK_URL` - Discord webhook URL for notifications (If you don't know what this is, see: [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
> If you do not provide the optional secrets, the workflow will still function normally, but related features will be skipped.

> Note: Typically, the six cookies used will have a validity of one year. In case of login or authentication errors, you should repeat the cookie retrieval steps and update the secrets with the new values.

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
- Repository logs (logs are stored in the `logs` branch of the repository)

## Troubleshooting

- **Actions not running**: Verify workflows are enabled and secrets are configured
- **Check-in failures**: Update expired cookies in secrets
- **Code redemption issues**: Check logs for specific error codes and rate limiting

## Contributing

This is a template repository. If you want to contribute improvements:
1. Fork the original template repository
2. Make your changes
3. Submit a pull request

## Disclaimer
This template is intended solely for personal use. Please ensure you comply with HoyoLab's terms of service when utilizing automated tools. While I have used this solution for an extended period without encountering any problems, I cannot be held responsible for any bans or issues that may result from using this template.