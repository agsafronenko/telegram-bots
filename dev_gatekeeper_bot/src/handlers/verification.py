import asyncio
import logging
import random
from telegram import Update, ChatPermissions
from telegram.ext import CallbackContext
from src.config import (CODING_QUESTIONS, TIMEOUT_SECONDS, send_welcome_msg, send_success_msg, send_fail_msg, send_timeout_msg)
from src.handlers.message_tracking import (
    track_bot_messages, 
    delete_bot_messages, 
    delete_user_messages,
    set_new_members
)

# Dictionary to store ongoing verification challenges
# Key: user_id
# Value: Contains verification details like chat_id, username, question, answer, and timeout task
pending_verifications = {}
new_members = []


async def verification_timeout(user_id: int, chat_id: int, context: CallbackContext) -> None:
    """Handle timeout for verification."""
    logger = logging.getLogger(__name__)
    
    await asyncio.sleep(TIMEOUT_SECONDS)  # Wait for TIMEOUT_SECONDS
    
    try:
        if user_id in pending_verifications:
            
            # Time's up: ban the user permanently
            await context.bot.ban_chat_member(
                chat_id=chat_id, 
                user_id=user_id,
                revoke_messages=True
            )
            
            timeout_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=send_timeout_msg(pending_verifications[user_id]["username"]),
                parse_mode='HTML'
            )

            await track_bot_messages(chat_id, timeout_msg.message_id)

            # Schedule deletion of verification messages
            asyncio.create_task(delete_bot_messages(context, chat_id))
            asyncio.create_task(delete_user_messages(context, chat_id, user_id))
            
            # Clean up
            del pending_verifications[user_id]
    except Exception as e:
        logger.error(f"Error in timeout handler: {e}")


async def on_new_chat_member(update: Update, context: CallbackContext) -> None:
    """Challenge new chat members with a programming question."""
    logger = logging.getLogger(__name__)
    
    for new_member in update.message.new_chat_members:
        # Skip the bot itself
        if new_member.id == context.bot.id:
            continue
            
        user_id = new_member.id
        set_new_members(user_id)
        username = update.effective_user.username
        chat_id = update.effective_chat.id
        
        # Select a random question
        question_data = random.choice(CODING_QUESTIONS)
        question = question_data["question"]
        answer = question_data["answer"]
        
        # Restrict the user from sending messages
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,  # Allow text messages for answering
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                )
            )
        except Exception as e:
            logger.error(f"Error restricting user: {e}")
            await update.message.reply_text("I couldn't restrict the new user. Please check my permissions.")
            return
        
        # Send the challenge
        
        welcome_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=send_welcome_msg(username, question),
            parse_mode='HTML'
        )

        await track_bot_messages(chat_id, welcome_msg.message_id)
        
        # Set up timeout
        timeout_task = asyncio.create_task(
            verification_timeout(user_id, chat_id, context)
        )
        
        # Store the verification data
        pending_verifications[user_id] = {
            "chat_id": chat_id,
            "username": username,
            "question": question,
            "answer": answer,
            "task": timeout_task
        }


async def check_answer(update: Update, context: CallbackContext) -> None:
    """Check if the user's answer is correct."""
    logger = logging.getLogger(__name__)
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Check if this user has a pending verification
    if user_id not in pending_verifications:
        return
    
    user_answer = update.message.text.strip()
    verification_data = pending_verifications[user_id]
    correct_answer = verification_data["answer"]
    chat_id = verification_data["chat_id"]
    
    # Cancel the timeout task
    if "task" in verification_data and not verification_data["task"].done():
        verification_data["task"].cancel()
    
    # Check if the answer is correct
    if user_answer.lower() == correct_answer.lower():
        # Restore permissions
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        # Send and track the success message
        success_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=send_success_msg(username),
            parse_mode='HTML'
        )
        await track_bot_messages(chat_id, success_msg.message_id)
        
        # Schedule deletion of verification messages
        asyncio.create_task(delete_bot_messages(context, chat_id))
        asyncio.create_task(delete_user_messages(context, chat_id, user_id))
    else:
        # Delete user's messages and ban them
        try:
         
            # Ban the user permanently
            await context.bot.ban_chat_member(
                chat_id=chat_id, 
                user_id=user_id,
                revoke_messages=True,
            )
            
            # Send and track the failure message
            fail_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=send_fail_msg(username),
                parse_mode='HTML'
            )
            await track_bot_messages(chat_id, fail_msg.message_id)
            
            # Schedule deletion of bot messages after 5 seconds
            asyncio.create_task(delete_bot_messages(context, chat_id))
            asyncio.create_task(delete_user_messages(context, chat_id, user_id))
            
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"<b>{username}</b> failed the verification, but I couldn't ban them or delete their messages. Please check my permissions.",
                parse_mode='HTML'
            )
   
    # Clean up
    del pending_verifications[user_id]
