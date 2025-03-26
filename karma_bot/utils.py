from datetime import datetime, timedelta

def adjust_time(scheduled_time):
    """
    Adjust scheduled time to UTC considering local timezone.
    
    Args:
        scheduled_time (str): Time in 24-hour format
    
    Returns:
        datetime.time: Adjusted time
    """
    # Get local timezone
    local_time = datetime.now().astimezone()

    # Get timezone difference with UTC in hours
    difference = local_time.utcoffset().total_seconds() / 3600
    
    # Convert scheduled time to datetime
    time_obj = datetime.strptime(scheduled_time, "%H:%M")
    
    # Subtract timezone difference
    adjusted_time = time_obj - timedelta(hours=difference)
    
    return adjusted_time.time()

def generate_leaderboard_message(top_users, is_daily=False):
    """
    Generate a leaderboard message from top users.
    
    Args:
        top_users (list): List of top users with their details
        is_daily (bool, optional): Flag to indicate daily leaderboard. Defaults to False.
    
    Returns:
        str: Formatted leaderboard message
    """
    title = "🌟 *Daily Reputation Leaderboard* 🌟\n\n" if is_daily else "🏆 *All-Time Top 10 Reputation Leaders* 🏆\n\n"
    rank_message = title

    for idx, (user_id, first_name, username, reputation) in enumerate(top_users, 1):
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(idx, '✨')
        
        # Create a tappable username link, fallback to first name or 'Anonymous'
        if username:
            user_display = f"[{first_name or username}](tg://user?id={user_id})"
        else:
            user_display = first_name or 'Anonymous'

        rank_message += f"{medal} {idx}. {user_display}: {reputation} points\n"
    
    return rank_message
