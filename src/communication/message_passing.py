"""
Message Passing Layer untuk inter-node communication
Support untuk asyncio-based networking
"""

import asyncio
import json
import pickle
from typing import Dict, Any, Optional, Callable
from loguru import logger
import aiohttp
from aiohttp import web

from ..utils.config import Config
from ..consensus.message import RaftMessage


class NetworkTransport:
    """Network transport abstraction"""
    
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.message_handler: Optional[Callable] = None
        
        # Setup routes
        self.app.router.add_post('/message', self._handle_message)
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/status', self._status_check)
    
    async def start(self):
        """Start network transport"""
        logger.info(f"Starting network transport on {self.host}:{self.port}")
        
        # Create client session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Network transport started successfully")
    
    async def stop(self):
        """Stop network transport"""
        logger.info("Stopping network transport")
        
        if self.session:
            await self.session.close()
        
        if self.runner:
            await self.runner.cleanup()
    
    async def send(self, target_host: str, target_port: int, 
                   message: RaftMessage) -> Optional[RaftMessage]:
        """Send message to target node"""
        if not self.session:
            logger.error("Session not initialized")
            return None
        
        url = f"http://{target_host}:{target_port}/message"
        
        try:
            # Serialize message
            data = message.to_dict()
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return RaftMessage.from_dict(response_data)
                else:
                    logger.warning(f"Failed to send message: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout sending message to {target_host}:{target_port}")
            return None
        except Exception as e:
            logger.error(f"Error sending message to {target_host}:{target_port}: {e}")
            return None
    
    async def _handle_message(self, request: web.Request) -> web.Response:
        """Handle incoming message"""
        try:
            data = await request.json()
            message = RaftMessage.from_dict(data)
            
            # Call message handler if registered
            if self.message_handler:
                response = await self.message_handler(message)
                if response:
                    return web.json_response(response.to_dict())
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({'status': 'healthy', 'node_id': self.node_id})
    
    async def _status_check(self, request: web.Request) -> web.Response:
        """Status check endpoint"""
        return web.json_response({
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port
        })
    
    def set_message_handler(self, handler: Callable):
        """Set message handler callback"""
        self.message_handler = handler


class MessagePassingLayer:
    """High-level message passing layer"""
    
    def __init__(self, node_id: str, cluster_nodes: Dict[str, Dict[str, Any]]):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.transport: Optional[NetworkTransport] = None
        
        # Message queue
        self.pending_messages: asyncio.Queue = asyncio.Queue()
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.failures = 0
    
    async def start(self, host: str, port: int):
        """Start message passing layer"""
        self.transport = NetworkTransport(self.node_id, host, port)
        await self.transport.start()
        logger.info(f"Message passing layer started for {self.node_id}")
    
    async def stop(self):
        """Stop message passing layer"""
        if self.transport:
            await self.transport.stop()
    
    async def send_message(self, target_id: str, message: RaftMessage) -> Optional[RaftMessage]:
        """Send message to target node"""
        if target_id not in self.cluster_nodes:
            logger.error(f"Unknown target node: {target_id}")
            return None
        
        target = self.cluster_nodes[target_id]
        target_host = target['host']
        target_port = target['port']
        
        try:
            response = await self.transport.send(target_host, target_port, message)
            self.messages_sent += 1
            return response
        except Exception as e:
            self.failures += 1
            logger.error(f"Failed to send message to {target_id}: {e}")
            return None
    
    async def broadcast_message(self, message: RaftMessage) -> Dict[str, Optional[RaftMessage]]:
        """Broadcast message to all nodes"""
        responses = {}
        tasks = []
        
        for node_id in self.cluster_nodes.keys():
            task = asyncio.create_task(self.send_message(node_id, message))
            tasks.append((node_id, task))
        
        for node_id, task in tasks:
            try:
                response = await task
                responses[node_id] = response
            except Exception as e:
                logger.error(f"Error broadcasting to {node_id}: {e}")
                responses[node_id] = None
        
        return responses
    
    def set_message_handler(self, handler: Callable):
        """Set message handler"""
        if self.transport:
            self.transport.set_message_handler(handler)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get messaging statistics"""
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'failures': self.failures
        }
