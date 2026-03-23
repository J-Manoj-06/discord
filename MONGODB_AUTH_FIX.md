🔧 MONGODB AUTHENTICATION ERROR - QUICK FIX
═════════════════════════════════════════════════════════════════════

You're getting: "bad auth : Authentication failed."

This means the MongoDB credentials or access is blocked.

─────────────────────────────────────────────────────────────────
STEP 1: Verify MongoDB Connection String
─────────────────────────────────────────────────────────────────

Go to: https://www.mongodb.com/cloud/atlas

1. Find your cluster
2. Click "Connect"
3. Choose: "Connect with MongoDB Shell" or "Python" 
4. Copy the connection string

Your string should look like:
   mongodb+srv://username:password@clustername.mongodb.net/database

⚠️  Key things to check:
   - Username is correct (with special chars escaped if needed)
   - Password is correct (with special chars escaped if needed)  
   - Cluster name matches exactly
   - /database part should match your actual database name

─────────────────────────────────────────────────────────────────
STEP 2: Fix Special Characters in Password
─────────────────────────────────────────────────────────────────

If your MongoDB password has special characters (!@#$%^&*), 
they need to be URL-encoded:

CHARACTER TO ENCODE:
  ! → %21
  @ → %40
  # → %23
  $ → %24
  % → %25
  ^ → %5E
  & → %26
  * → %2A
  ( → %28
  ) → %29

Example:
   Before: mongodb+srv://user:pass@word!@cluster.mongodb.net/db
   After:  mongodb+srv://user:pass%40word%21@cluster.mongodb.net/db

─────────────────────────────────────────────────────────────────
STEP 3: Check IP Whitelist
─────────────────────────────────────────────────────────────────

1. Log into MongoDB Atlas
2. Click your cluster
3. Go to: Security → Network Access
4. Check the IP list

For development, easiest is to add: 0.0.0.0/0 (all IPs)
Later, add only your server IP for production.

NOTE: After updating whitelist, you may need to wait 1-2 minutes
for it to take effect.

─────────────────────────────────────────────────────────────────
STEP 4: Update .env and Test
─────────────────────────────────────────────────────────────────

Edit .env with corrected URI:

   nano .env

Update MONGODB_URI= line with correct connection string.
Save: Ctrl+X, Y, Enter

Then test:

   source .venv/bin/activate
   python main.py

─────────────────────────────────────────────────────────────────
IF STILL NOT WORKING:
─────────────────────────────────────────────────────────────────

1. Create a new MongoDB test user:
   Atlas → Security → Database Access
   → Add New User
   → Create simple user (abc123 password)
   → Make sure it has read/write to any database
   → Build URI with this new user

2. Or, reset your cluster and start fresh

3. Check MongoDB status: Atlas → Cluster → Overview
   Should show "Active" status

4. Try connecting to MongoDB directly:
   mongosh "your_connection_string"
   If this fails, Atlas portal confirms the issue

─────────────────────────────────────────────────────────────────
MONGODB CONNECT STRING GENERATOR:
─────────────────────────────────────────────────────────────────

Format:
   mongodb+srv://[username]:[password]@[clustername].mongodb.net/[database]?retryWrites=true&w=majority

Example:
   mongodb+srv://admin:MyPassword123@mycluster.mongodb.net/discord_bot?retryWrites=true&w=majority

─────────────────────────────────────────────────────────────────

Your current error shows the bot IS connecting and trying to auth.
So MongoDB server is reachable - just credentials/whitelist issue.

Fix the 3 steps above and try again!
