import asyncio
import logging
from telegram import Update
from telegram.ext import CallbackContext
from src.config import DELAY


# Global dictionary to track newly joined members
# Stores user IDs of members who need to complete verification
new_members = []

# Global dictionary to track messages sent by new (unverified) users
# Allows for targeted message deletion after verification/ban
user_messages = {}

# Global dictionary to track messages sent by the bot during verification
# Enables cleanup of bot-generated messages
bot_messages = {}


def set_new_members(member):
    """
    Add a newly joined member to the tracking list.
    
    This helps identify which users are in the verification process
    and need special message handling.
    
    Args:
        member (int): User ID of the newly joined member
    """
    global new_members
    new_members.append(member)


async def track_messages(update: Update, context: CallbackContext) -> None:
    """
    Track messages from new (unverified) members.
    
    Only records messages from users who are in the verification process.
    Stores message IDs to enable later deletion.
    """
    user_id = update.effective_user.id 
    if user_id not in new_members:
        return
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    
    if user_id not in user_messages:
        user_messages[user_id] = {"chat_id": chat_id, "messages": []}
    
    user_messages[user_id]["messages"].append(message_id)


async def track_bot_messages(chat_id: int, message_id: int) -> None:
    """
    Track messages sent by the bot during the verification process.
    
    Stores bot message IDs to enable later deletion and cleanup.
    
    Args:
        chat_id (int): ID of the chat where the message was sent
        message_id (int): ID of the bot's message
    """
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    bot_messages[chat_id].append(message_id)


async def delete_bot_messages(context: CallbackContext, chat_id: int) -> None:
    """Delete messages sent by the bot."""
    logger = logging.getLogger(__name__)
    
    
    if chat_id in bot_messages:
        for message_id in bot_messages[chat_id]:
            try:
                await asyncio.sleep(DELAY)
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.error(f"Failed to delete bot message: {e}")
        
        # Clear the tracked bot messages
        del bot_messages[chat_id]


async def delete_user_messages(context: CallbackContext, chat_id: int, user_id: int) -> None:
    """Delete all tracked messages from a user in a chat."""
    logger = logging.getLogger(__name__)
    
    if user_id in user_messages and user_messages[user_id]["chat_id"] == chat_id:
        messages_to_delete = user_messages[user_id]["messages"]
        
        for msg_id in messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Failed to delete message {msg_id}: {e}")
        
        # Clear the tracked user messages
        del user_messages[user_id]
