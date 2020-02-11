# Hostel Hunt

**SUTD Hostel Hunt 2020 Telegram Bot**

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/jamestiotio/hostelhunt)

## Usage

- `/start` to start the bot.
- `/help` to display usage help text for the bot.
- `/register` to register as a participant using your student ID.
- `/hint` to ask the bot for hints.
- `/claim <token>` to attempt to claim the specified token.

Several hidden administrative commands with restricted access are also available.

## Repository Details

**Heroku App Config Vars:**

``` json
{
  "env": {
    "ADMIN_LIST": "[<user-id-1>, <user-id-2>, ...]",
    "TELEGRAM_TOKEN": "<id>:<token>",
    "SUTD_AUTH": "['<group-leader-1-token>', '<group-leader-2-token>', ...]",
    "MASTER_TOKEN": "<user-id>",
    "TZ": "Asia/Singapore",
    "WEBHOOK_URL": "https://<app-name>.herokuapp.com/",
    "GOOGLE_APPLICATION_CREDENTIALS": "<firestore-config-file-path>.json"
  }
}
```

Deploy the bot by running the command `python3 app.py`.

Finally, issue an HTTPS request to `https://api.telegram.org/bot<id>:<token>/setWebhook?url=https://<app-name>.herokuapp.com/<id>:<token>` to enable the webhook for the bot.

Sample Firebase data is available [here](./sutd-hostel-hunt-bot.json).

Oh and if you expected to find any hints or tokens here, you are in for a disappointment. It's all in the Firestore database. No cheating! 😉

## Documentation

More details on the bot will be elaborated here soon!

## Acknowledgements

Credits to [@2manslkh](https://github.com/2manslkh) for the initial version of this SUTD Hostel Hunt Telegram Bot. I changed the MySQL parts to implement Firebase connectivity instead, as well as improved a few features of the bot and added a few more comments for code clarity.
