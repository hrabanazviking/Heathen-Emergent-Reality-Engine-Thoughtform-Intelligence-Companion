"""
Norse Saga Engine - Cosmological Communication Matrix

Models information flows between:
1) Nine Worlds (Asgard, Midgard, etc.)
2) Deities (Odin, Freyja, Saga, Norns)
3) Systems (Wyrd, Dreams, Story)
"""

import logging
from enum import Enum
from typing import Any, Deque, Dict, List, Sequence, Tuple
from collections import deque
from threading import Lock
from time import time

logger = logging.getLogger("yggdrasil.communications")


class Realm(Enum):
    ASGARD = "Asgard"
    MIDGARD = "Midgard"
    ALFHEIM = "Alfheim"
    HELHEIM = "Helheim"
    JOTUNHEIM = "Jotunheim"
    MUSPELHEIM = "Muspelheim"
    NIFLHEIM = "Niflheim"
    SVARTALFHEIM = "Svartalfheim"
    VANAHEIM = "Vanaheim"


class Deity(Enum):
    ODIN = "Odin"
    FREYJA = "Freyja"
    SAGA = "Saga"
    NORNS = "Norns"


class System(Enum):
    WYRD = "Wyrd"
    DREAMS = "Dreams"
    STORY = "Story"


class MessageType(Enum):
    DIVINE_COMMAND = "Divine Command"
    FATE_THREAD = "Fate Thread"
    DREAM_VISION = "Dream Vision"
    STORY_FRAGMENT = "Story Fragment"
    EMOTIONAL_PULSE = "Emotional Pulse"
    RUNE_ECHO = "Rune Echo"


class CommunicationPathway:
    """Bidirectional pathway between entities"""

    def __init__(
        self,
        source: Tuple[Realm, Deity, System],
        destination: Tuple[Realm, Deity, System],
        message_types: List[MessageType],
    ):
        self.source = source
        self.destination = destination
        self.message_types = message_types
        self.message_queue: Deque[Dict[str, Any]] = deque(maxlen=256)
        self._lock = Lock()

    def send_message(self, message_type: MessageType, content: Dict):
        """Queue a message for transmission"""
        if message_type not in self.message_types:
            raise ValueError(
                f"Unsupported message type: {message_type} for this pathway"
            )
        with self._lock:
            self.message_queue.append({"type": message_type, "content": content, "ts": time()})

        # Log message transmission
        src = self._format_entity(self.source)
        dest = self._format_entity(self.destination)

        # Generate literal log for the Sacred Well stream
        literal_msg = f"[{src}->{dest}] {message_type.value}: {str(content)[:100]}..."
        logger.info(literal_msg)

    def _format_entity(self, entity: Tuple[Realm, Deity, System]) -> str:
        """Format entity tuple for logging"""
        parts = []
        if entity[0]:
            parts.append(entity[0].value)
        if entity[1]:
            parts.append(entity[1].value)
        if entity[2]:
            parts.append(entity[2].value)
        return "/".join(parts) if parts else "Cosmos"

    def receive_messages(self):
        """Retrieve all queued messages"""
        with self._lock:
            messages = list(self.message_queue)
            self.message_queue.clear()
            return messages


class CosmologicalMatrix:
    """Core communication matrix connecting all entities"""

    def __init__(self, emotion_service):
        self.pathways: List[CommunicationPathway] = []
        self.pathway_index: Dict[Tuple[Any, Any], List[CommunicationPathway]] = {}
        self.emotion_service = emotion_service
        self._initialize_core_pathways()

    def _initialize_core_pathways(self):
        """Create canonical pathways based on Norse mythology"""
        # 1. Odin's pathways
        self.add_pathway(
            source=(Realm.ASGARD, Deity.ODIN, None),
            destination=(None, None, System.WYRD),
            message_types=[MessageType.DIVINE_COMMAND, MessageType.FATE_THREAD],
        )

        # 2. Freyja's pathways
        self.add_pathway(
            source=(Realm.VANAHEIM, Deity.FREYJA, None),
            destination=(None, None, System.DREAMS),
            message_types=[MessageType.EMOTIONAL_PULSE, MessageType.DREAM_VISION],
        )

        # 3. Norns' pathways
        self.add_pathway(
            source=(None, Deity.NORNS, None),
            destination=(None, None, System.WYRD),
            message_types=[MessageType.FATE_THREAD],
        )

        # 4. Saga's pathways
        self.add_pathway(
            source=(Realm.ASGARD, Deity.SAGA, None),
            destination=(None, None, System.STORY),
            message_types=[MessageType.STORY_FRAGMENT],
        )

        # 5. Saga-Odin lore channel (RAG system)
        self.add_pathway(
            source=(Realm.ASGARD, Deity.SAGA, None),
            destination=(Realm.ASGARD, Deity.ODIN, None),
            message_types=[MessageType.STORY_FRAGMENT, MessageType.DIVINE_COMMAND],
        )

        # 6. Norns' fate weaving connection
        self.add_pathway(
            source=(None, Deity.NORNS, None),
            destination=(None, None, System.WYRD),
            message_types=[MessageType.FATE_THREAD, MessageType.RUNE_ECHO],
        )

        # 7. Dream system integration
        self.add_pathway(
            source=(None, None, System.DREAMS),
            destination=(None, None, System.WYRD),
            message_types=[MessageType.DREAM_VISION, MessageType.EMOTIONAL_PULSE],
        )

        # 8. Emotional pulse broadcasting
        self.add_pathway(
            source=(None, Deity.FREYJA, None),
            destination=(None, None, System.WYRD),
            message_types=[MessageType.EMOTIONAL_PULSE],
        )

        # 9-12. Yggdrasil connections
        for realm in Realm:
            self.add_pathway(
                source=(realm, None, None),
                destination=(None, None, System.WYRD),
                message_types=[MessageType.RUNE_ECHO],
            )

    def add_pathway(
        self,
        source: Tuple[Realm, Deity, System],
        destination: Tuple[Realm, Deity, System],
        message_types: List[MessageType],
    ):
        """Add a bidirectional pathway, merging message_types if already registered."""
        # If this source→destination pair already exists, merge message_types rather
        # than creating duplicate pathway objects (prevents duplicate message delivery).
        existing = self.pathway_index.get((source, destination))
        if existing:
            for mt in message_types:
                if mt not in existing[0].message_types:
                    existing[0].message_types.append(mt)
            # Also update reverse pathway
            existing_rev = self.pathway_index.get((destination, source))
            if existing_rev:
                for mt in message_types:
                    if mt not in existing_rev[0].message_types:
                        existing_rev[0].message_types.append(mt)
            return

        pathway = CommunicationPathway(source, destination, message_types)
        self.pathways.append(pathway)

        # Create reverse pathway
        reverse_pathway = CommunicationPathway(destination, source, message_types)
        self.pathways.append(reverse_pathway)

        self.pathway_index.setdefault((source, destination), []).append(pathway)
        self.pathway_index.setdefault((destination, source), []).append(reverse_pathway)

    def process_emotional_pulse(self, emotion_vector: Sequence[float]):
        """Convert emotional state to cosmological message"""
        rune = self.emotion_service.tag_emotion_state(emotion_vector)
        vector = (
            emotion_vector.tolist()
            if hasattr(emotion_vector, "tolist")
            else list(emotion_vector)
        )
        return {"rune": rune, "vector": vector}

    def send_emotional_update(self, emotion_vector: Sequence[float]):
        """Broadcast emotional state through relevant pathways"""
        pulse = self.process_emotional_pulse(emotion_vector)
        for pathway in self.pathways:
            if MessageType.EMOTIONAL_PULSE in pathway.message_types:
                pathway.send_message(MessageType.EMOTIONAL_PULSE, pulse)


    def publish(
        self,
        source: Tuple[Realm, Deity, System],
        destination: Tuple[Realm, Deity, System],
        message_type: MessageType,
        content: Dict[str, Any],
    ) -> int:
        """Send a message to all matching pathways and return delivery count."""
        deliveries = 0
        for pathway in self.pathway_index.get((source, destination), []):
            if message_type in pathway.message_types:
                pathway.send_message(message_type, content)
                deliveries += 1
        return deliveries
