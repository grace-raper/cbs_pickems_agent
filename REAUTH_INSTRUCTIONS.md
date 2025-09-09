# CBS Pickem Reauthentication Instructions

## Authentication Failed

Your CBS Pickem authentication has expired or is invalid. This is normal and happens periodically (usually every 1-2 weeks) due to CBS Sports security policies.

## How to Reauthenticate

Follow these simple steps to reauthenticate:

1. **Open Terminal** and navigate to your CBS Pickem directory:
   ```bash
   cd /Users/graceraper/Repositories/cbs_playwright_login
   ```

2. **Run the login script**:
   ```bash
   python login.py
   ```

3. **Complete the authentication process**:
   - A browser window will open automatically
   - Enter your CBS Sports credentials
   - Complete any CAPTCHA or verification steps if required
   - The script will automatically save your new authentication cookies

4. **Verify authentication was successful**:
   ```bash
   python check_session.py
   ```
   If successful, you'll see a confirmation message and the CBS Pickem page will load.

5. **Run the workflow again**:
   ```bash
   python run_local_workflow.py
   ```

## Troubleshooting

If you encounter any issues during reauthentication:

- **Check your internet connection** - Make sure you're connected to the internet
- **Verify your credentials** - Ensure your CBS Sports username and password are correct
- **Check the logs** - Review `cbs_pickem_workflow.log` for detailed error information
- **Manual login** - If automated login fails, try logging in manually through the browser and then run `check_session.py` again

## Need More Help?

If you continue to experience issues, check the [LOGIN_NOTES.md](LOGIN_NOTES.md) file for additional troubleshooting steps and information about CBS Sports authentication requirements.
