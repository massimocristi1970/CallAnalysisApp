# How to Change from Local Machine Server to Supabase

## Summary

Your Call Analysis App has been updated to support **both** local SQLite database and Supabase (cloud PostgreSQL). You can now choose which one to use!

## Current Status

✅ **The migration is COMPLETE** - Your app now supports Supabase!

The repository has been updated with:
1. **Hybrid database layer** - Works with both SQLite and Supabase
2. **Environment configuration** - Easy switching between databases
3. **Complete documentation** - Step-by-step guides for setup and migration
4. **Backward compatibility** - Existing setup continues to work unchanged

## What Changed?

### Files Modified:
- `database.py` - Now supports both SQLite and Supabase
- `requirements.txt` - Added `supabase` and `python-dotenv` dependencies
- `.gitignore` - Protected sensitive `.env` file
- `README.md` - Added database options section

### Files Added:
- `.env.example` - Template for Supabase credentials
- `SUPABASE_SETUP.md` - Detailed setup guide
- `QUICK_START_SUPABASE.md` - 5-minute quick start
- `MIGRATION_GUIDE.md` - Data migration instructions

## How to Use Supabase (3 Options)

### Option 1: Quick Start (Recommended for Testing) - 5 Minutes

Follow the guide: [QUICK_START_SUPABASE.md](QUICK_START_SUPABASE.md)

**TL;DR:**
1. Create free Supabase account at https://supabase.com
2. Create new project, run SQL schema (provided in guide)
3. Copy credentials to `.env` file
4. Run the app!

### Option 2: Detailed Setup (Recommended for Production)

Follow the guide: [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

Includes:
- Complete setup instructions
- Row Level Security (RLS) configuration
- Best practices for production
- Troubleshooting guide

### Option 3: Migrate Existing Data

Follow the guide: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

If you have existing data in SQLite that you want to move to Supabase.

## Architecture Overview

### Before (Local Only)
```
[Streamlit App] → [SQLite Database File]
                   (call_analysis.db)
```

### After (Your Choice!)
```
[Streamlit App] → [Database Abstraction Layer]
                         ↓
                    ┌────┴────┐
                    ↓         ↓
            [SQLite]    [Supabase]
            (local)     (cloud PostgreSQL)
```

The app automatically uses:
- **Supabase** if `.env` is configured with credentials
- **SQLite** if Supabase is not configured (default)

## Configuration

### To Use Local SQLite (Current Default)
**No changes needed!** It works automatically.

Or explicitly set in `.env`:
```env
USE_LOCAL_DB=true
```

### To Use Supabase
Create `.env` file:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
USE_LOCAL_DB=false
```

### To Switch Between Them
Just change `USE_LOCAL_DB` in `.env` and restart the app!

## Key Features

### With SQLite:
✅ No configuration needed  
✅ Works offline  
✅ Simple single-user setup  
✅ Fast for small datasets  
✅ No costs  

### With Supabase:
✅ Cloud-based - access from anywhere  
✅ Multi-user support  
✅ Professional database UI  
✅ Automatic backups (paid plans)  
✅ Better for large datasets  
✅ Real-time capabilities (future)  
✅ Free tier available (500MB database)  

## Installation

### New Installation:
```bash
# Install dependencies
pip install -r requirements.txt

# For Supabase support
pip install supabase python-dotenv

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Existing Installation:
```bash
# Just add the new dependencies
pip install supabase python-dotenv
```

## Usage Examples

### Start with SQLite (Default)
```bash
streamlit run app.py
```
Output:
```
✓ Using local SQLite database
```

### Start with Supabase
1. Create `.env` with your Supabase credentials
2. Run:
```bash
streamlit run app.py
```
Output:
```
✓ Connected to Supabase database
✓ Supabase tables verified
```

## Database Schema

The same schema works for both backends:

- **agents** - Agent information (name, department, etc.)
- **calls** - Call recordings and transcripts
- **keywords** - Detected keywords with confidence scores
- **qa_scores** - Quality assurance scores
- **monthly_summaries** - Performance summaries by month

## Benefits of This Approach

1. **Flexible**: Choose what works best for you
2. **Safe**: Existing setup continues working
3. **Easy**: Switch between databases anytime
4. **Future-proof**: Can start local, move to cloud later
5. **No lock-in**: Can migrate back if needed

## Common Questions

### Q: Do I have to migrate?
**A:** No! Your app works exactly as before with SQLite. Supabase is optional.

### Q: Can I try Supabase without losing my data?
**A:** Yes! Your SQLite data stays intact. You can switch back anytime.

### Q: How much does Supabase cost?
**A:** Free tier includes 500MB database, 2GB bandwidth/month. More than enough for testing!

### Q: Is my data secure with Supabase?
**A:** Yes! Supabase uses PostgreSQL with encryption. You can configure Row Level Security (RLS) for additional protection. See SUPABASE_SETUP.md for details.

### Q: Can multiple users access the same Supabase database?
**A:** Yes! That's one of the benefits of Supabase. Configure proper authentication for production use.

### Q: What if Supabase is down?
**A:** You can switch back to SQLite by changing `USE_LOCAL_DB=true` in `.env`.

## Next Steps

1. **Try it locally first** - Make sure everything works with SQLite
2. **Create Supabase account** - Free tier is perfect for testing
3. **Follow quick start** - Get Supabase running in 5 minutes
4. **Test with sample data** - Process a few calls to verify
5. **Migrate data (optional)** - Move existing data if desired
6. **Configure for production** - Set up RLS, backups, monitoring

## Support

- **Supabase Issues**: https://github.com/supabase/supabase/discussions
- **App Issues**: Create an issue in this repository
- **Questions**: Check the documentation files:
  - QUICK_START_SUPABASE.md
  - SUPABASE_SETUP.md
  - MIGRATION_GUIDE.md

## Technical Details

### Code Changes Summary:
- Database layer abstracted to support multiple backends
- All queries adapted to work with both SQLite and PostgreSQL
- Environment-based configuration
- Graceful fallback mechanism
- Zero breaking changes to existing code

### Testing:
- ✅ SQLite backward compatibility verified
- ✅ Supabase connection tested
- ✅ Graceful fallback tested
- ✅ Database operations validated
- ✅ Security scan passed (0 alerts)

## Conclusion

Your repository now fully supports Supabase! You have:

1. ✅ **Working implementation** - Database layer supports both SQLite and Supabase
2. ✅ **Complete documentation** - Multiple guides for different needs
3. ✅ **Easy configuration** - Simple `.env` file setup
4. ✅ **Backward compatibility** - Existing setup unchanged
5. ✅ **Migration tools** - Scripts to move data between databases

**Choose your path:**
- Keep using SQLite (no changes needed)
- Try Supabase (5-minute setup)
- Migrate data later (when ready)

The choice is yours! 🚀
