"""
Norns' Wyrd Weaving Fate System Integration

Connects cosmological communication pathways to the fate system
"""

import logging
from typing import Dict, Any
from ..yggdrasil_core import tree

logger = logging.getLogger(__name__)

class FateWeaver:
    """Handles integration between Norns pathway and fate system"""
    def __init__(self):
        self.matrix = tree.state.setdefault('cosmological_matrix', {})
        self.fate_system = tree.state.get('fate_system')
        if self.fate_system is None:
            raise RuntimeError(
                "fate_system not found in tree.state; ensure Yggdrasil initialises "
                "fate_system before FateWeaver is constructed."
            )
        
    def process_fate_thread(self, message: Dict[str, Any]):
        """Process fate thread messages from Norns"""
        if not isinstance(message, dict):
            logger.warning("process_fate_thread received non-dict message: %s", type(message))
            return
        thread_data = message.get("content")
        if not isinstance(thread_data, dict):
            logger.warning("process_fate_thread: missing or invalid 'content' field")
            return

        action = thread_data.get("action", "")
        thread_id = thread_data.get("id")

        # Create new fate thread
        if action == "weave":
            if thread_id is None:
                logger.warning("process_fate_thread 'weave': missing 'id'")
                return
            self.fate_system.create_thread(
                thread_id,
                thread_data.get("entities", []),
                thread_data.get("probability", 0.5),
                thread_data.get("consequences", [])
            )

        # Modify existing fate thread
        elif action == "adjust":
            if thread_id is None:
                logger.warning("process_fate_thread 'adjust': missing 'id'")
                return
            self.fate_system.adjust_thread(
                thread_id,
                thread_data.get("new_probability"),
                thread_data.get("new_consequences")
            )

        # Sever fate thread
        elif action == "sever":
            if thread_id is None:
                logger.warning("process_fate_thread 'sever': missing 'id'")
                return
            self.fate_system.sever_thread(thread_id)
        
    def broadcast_fate_update(self, thread_id: str):
        """Broadcast fate updates to all realms"""
        thread = self.fate_system.get_thread(thread_id)
        if not thread:
            return
            
        message = {
            "type": tree.config['message_types']['FATE_THREAD'],
            "content": {
                "thread_id": thread_id,
                "status": thread.status,
                "probability": thread.probability,
                "entities": thread.entities
            }
        }
        
        # Send to all Yggdrasil-connected realms via matrix, or fall back to message queue
        for realm in tree.config.get('realms', []):
            if hasattr(self.matrix, 'send_to_realm'):
                self.matrix.send_to_realm(realm, message)
            else:
                try:
                    from core.message_queue import get_queue
                    queue = get_queue(f"realm_{realm}")
                    if queue:
                        queue.enqueue(message)
                except Exception as exc:
                    logger.warning("Could not broadcast fate update to realm %s: %s", realm, exc)

    def connect_to_norns_pathway(self):
        """Register handler for Norns pathway messages"""
        if hasattr(self.matrix, 'get_pathway'):
            norns_pathway = self.matrix.get_pathway(
                source=(None, tree.config['deities']['NORNS'], None),
                destination=(None, None, tree.config['systems']['WYRD'])
            )
            if hasattr(norns_pathway, 'register_handler'):
                norns_pathway.register_handler(
                    tree.config['message_types']['FATE_THREAD'],
                    self.process_fate_thread
                )