"""
Frontdesk HITL Backend API
Handles help requests, supervisor responses, and knowledge base management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import logging
import os
from typing import Optional, Dict, List
import json
import re

# Database (using simple in-memory for demo)
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Enums
class RequestStatus(Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    EXPIRED = "expired"

# Data models
@dataclass
class HelpRequest:
    id: str
    question: str
    caller_name: str
    caller_phone: str
    call_id: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    answer: Optional[str] = None
    timeout_at: Optional[datetime] = None
    supervisor_id: Optional[str] = None

@dataclass
class KnowledgeEntry:
    id: str
    question: str
    answer: str
    learned_at: datetime
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    source: str = "supervisor_response"

# In-memory storage
help_requests: Dict[str, HelpRequest] = {}
knowledge_base: Dict[str, KnowledgeEntry] = {}
request_history: List[Dict] = []

# Initialize with some sample knowledge
def init_knowledge_base():
    """Initialize with basic business information"""
    initial_knowledge = [
        {
            "question": "What are your hours?",
            "answer": "We're open Monday-Friday 9am-8pm, Saturday 10am-6pm, and closed on Sunday."
        },
        {
            "question": "Where are you located?",
            "answer": "We're located at 123 Main Street in Downtown, right next to City Hall."
        },
        {
            "question": "What services do you offer?",
            "answer": "We offer haircuts, hair coloring, styling, manicures, pedicures, facials, and massage therapy."
        },
        {
            "question": "How do I book an appointment?",
            "answer": "You can book by calling us at (555) 123-4567 or through our website at glamoursalon.com/book"
        }
    ]
    
    for kb in initial_knowledge:
        entry = KnowledgeEntry(
            id=f"kb_{uuid.uuid4().hex[:8]}",
            question=kb["question"],
            answer=kb["answer"],
            learned_at=datetime.now(),
            usage_count=0,
            source="initial_config"
        )
        knowledge_base[entry.id] = entry
    
    logger.info(f"Initialized knowledge base with {len(initial_knowledge)} entries")

init_knowledge_base()

# Helper functions
def log_action(request_id: str, action: str, actor: str, metadata: Dict = None):
    """Log request actions for audit trail"""
    history_entry = {
        "id": f"hist_{uuid.uuid4().hex[:8]}",
        "request_id": request_id,
        "action": action,
        "actor": actor,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    request_history.append(history_entry)
    logger.info(f"Action logged: {action} on {request_id} by {actor}")

def check_expired_requests():
    """Check and update expired requests"""
    now = datetime.now()
    expired_count = 0
    
    for req_id, req in help_requests.items():
        if req.status == RequestStatus.PENDING.value and req.timeout_at and now > req.timeout_at:
            req.status = RequestStatus.EXPIRED.value
            log_action(req_id, "expired", "system")
            logger.warning(f"Request {req_id} expired")
            expired_count += 1
    
    return expired_count

def search_knowledge_base(query: str, threshold: float = 0.25) -> Optional[KnowledgeEntry]:
    """
    Search knowledge base with improved matching
    Handles synonyms and similar questions
    """
    query_lower = query.lower().strip()
    best_match = None
    best_score = 0
    
    # Remove punctuation
    query_clean = re.sub(r'[^\w\s]', '', query_lower)
    
    # Synonym mapping for common words
    synonyms = {
        'hours': ['timings', 'time', 'schedule', 'open', 'close', 'opening', 'closing', 'timing'],
        'location': ['address', 'where', 'place', 'directions', 'find', 'located'],
        'services': ['offer', 'do', 'provide', 'available', 'have'],
        'price': ['cost', 'charge', 'fee', 'rates', 'expensive', 'cheap'],
        'appointment': ['booking', 'book', 'reserve', 'schedule'],
        'parking': ['park', 'car'],
        'payment': ['pay', 'card', 'cash', 'accept'],
    }
    
    # Expand query with synonyms
    query_words = set(query_clean.split())
    expanded_query = set(query_words)
    
    for word in query_words:
        for key, syn_list in synonyms.items():
            if word in syn_list or word == key:
                expanded_query.add(key)
                expanded_query.update(syn_list)
    
    # Remove stop words
    stop_words = {'what', 'when', 'where', 'who', 'how', 'is', 'are', 'do', 'does', 
                  'can', 'could', 'would', 'should', 'the', 'a', 'an', 'your', 'my',
                  'i', 'me', 'you', 'we', 'they', 'may', 'know', 'tell', 'get'}
    
    expanded_query = {w for w in expanded_query if w not in stop_words and len(w) > 2}
    
    logger.info(f"🔍 Searching for: '{query}' → Keywords: {expanded_query}")
    
    for kb_entry in knowledge_base.values():
        question_lower = kb_entry.question.lower()
        question_clean = re.sub(r'[^\w\s]', '', question_lower)
        
        # Check for exact match first
        if query_lower in question_lower or question_lower in query_lower:
            best_match = kb_entry
            best_score = 1.0
            logger.info(f"✅ Exact match: '{kb_entry.question}'")
            break
        
        # Get question words
        question_words = set(question_clean.split())
        question_words = {w for w in question_words if w not in stop_words and len(w) > 2}
        
        # Expand question words with synonyms
        expanded_question = set(question_words)
        for word in question_words:
            for key, syn_list in synonyms.items():
                if word in syn_list or word == key:
                    expanded_question.add(key)
                    expanded_question.update(syn_list)
        
        # Calculate overlap
        if len(expanded_query) == 0 or len(expanded_question) == 0:
            continue
        
        intersection = expanded_query.intersection(expanded_question)
        union = expanded_query.union(expanded_question)
        
        # Jaccard similarity
        score = len(intersection) / len(union) if len(union) > 0 else 0
        
        # Boost for matching important words
        important_matches = intersection.intersection({'hours', 'location', 'services', 'price'})
        if important_matches:
            score += 0.4
        
        if score > best_score:
            best_score = score
            best_match = kb_entry
            logger.info(f"📊 Candidate: '{kb_entry.question}' score={score:.2f}")
    
    if best_score >= threshold:
        best_match.usage_count += 1
        best_match.last_used_at = datetime.now()
        logger.info(f"✅ MATCH: '{best_match.question}' (score: {best_score:.2f})")
        return best_match
    
    logger.info(f"❌ NO MATCH for: '{query}' (best score: {best_score:.2f})")
    return None

def notify_customer(caller_phone: str, caller_name: str, answer: str):
    """Send notification to customer (simulated)"""
    message = f"Hi {caller_name}, here's the answer to your question: {answer}"
    
    logger.info("=" * 80)
    logger.info("📱 CUSTOMER NOTIFICATION")
    logger.info(f"To: {caller_phone}")
    logger.info(f"Message: {message}")
    logger.info("=" * 80)
    
    return True

def notify_supervisor(request: HelpRequest):
    """Notify supervisor of new help request"""
    logger.info("=" * 80)
    logger.info("🚨 SUPERVISOR NOTIFICATION")
    logger.info(f"New help request: {request.question}")
    logger.info(f"From: {request.caller_name} ({request.caller_phone})")
    logger.info(f"Request ID: {request.id}")
    logger.info("=" * 80)
    
    return True

# API Endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    check_expired_requests()
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "pending_requests": sum(1 for r in help_requests.values() if r.status == RequestStatus.PENDING.value),
            "total_requests": len(help_requests),
            "knowledge_entries": len(knowledge_base)
        }
    }), 200

@app.route('/api/requests', methods=['POST'])
def create_request():
    """Create a new help request from AI agent"""
    try:
        data = request.json
        
        required_fields = ['question', 'caller_name', 'caller_phone', 'call_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        now = datetime.now()
        
        help_request = HelpRequest(
            id=req_id,
            question=data['question'],
            caller_name=data['caller_name'],
            caller_phone=data['caller_phone'],
            call_id=data['call_id'],
            status=RequestStatus.PENDING.value,
            created_at=now,
            timeout_at=now + timedelta(hours=1)
        )
        
        help_requests[req_id] = help_request
        log_action(req_id, "created", "ai_agent", {"question": data['question']})
        
        notify_supervisor(help_request)
        
        logger.info(f"Created help request {req_id}: {data['question']}")
        
        return jsonify({
            "id": req_id,
            "status": "created",
            "message": "Help request created successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/requests', methods=['GET'])
def list_requests():
    """List help requests with optional filtering"""
    try:
        check_expired_requests()
        
        status_filter = request.args.get('status')
        
        results = []
        for req in help_requests.values():
            if status_filter and req.status != status_filter:
                continue
            
            req_dict = asdict(req)
            req_dict['created_at'] = req.created_at.isoformat()
            if req.resolved_at:
                req_dict['resolved_at'] = req.resolved_at.isoformat()
            if req.timeout_at:
                req_dict['timeout_at'] = req.timeout_at.isoformat()
            
            results.append(req_dict)
        
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            "requests": results,
            "count": len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing requests: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/requests/<request_id>', methods=['GET'])
def get_request(request_id: str):
    """Get specific request details"""
    try:
        if request_id not in help_requests:
            return jsonify({"error": "Request not found"}), 404
        
        req = help_requests[request_id]
        req_dict = asdict(req)
        req_dict['created_at'] = req.created_at.isoformat()
        if req.resolved_at:
            req_dict['resolved_at'] = req.resolved_at.isoformat()
        if req.timeout_at:
            req_dict['timeout_at'] = req.timeout_at.isoformat()
        
        return jsonify(req_dict), 200
        
    except Exception as e:
        logger.error(f"Error getting request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/requests/<request_id>/answer', methods=['POST'])
def answer_request(request_id: str):
    """Submit answer to help request"""
    try:
        if request_id not in help_requests:
            return jsonify({"error": "Request not found"}), 404
        
        data = request.json
        if 'answer' not in data:
            return jsonify({"error": "Missing answer field"}), 400
        
        req = help_requests[request_id]
        
        if req.status != RequestStatus.PENDING.value:
            return jsonify({"error": f"Request is already {req.status}"}), 400
        
        req.status = RequestStatus.RESOLVED.value
        req.answer = data['answer']
        req.resolved_at = datetime.now()
        req.supervisor_id = data.get('supervisor_id', 'supervisor')
        
        log_action(request_id, "answered", req.supervisor_id, {"answer": data['answer']})
        
        notify_customer(req.caller_phone, req.caller_name, data['answer'])
        
        kb_id = f"kb_{uuid.uuid4().hex[:8]}"
        kb_entry = KnowledgeEntry(
            id=kb_id,
            question=req.question,
            answer=data['answer'],
            learned_at=datetime.now(),
            usage_count=0,
            source="supervisor_response"
        )
        knowledge_base[kb_id] = kb_entry
        
        logger.info(f"Request {request_id} answered and added to knowledge base")
        logger.info("=" * 80)
        logger.info("📚 KNOWLEDGE BASE UPDATED")
        logger.info(f"New entry: {req.question}")
        logger.info(f"Answer: {data['answer']}")
        logger.info("=" * 80)
        
        return jsonify({
            "status": "success",
            "message": "Answer submitted and customer notified",
            "knowledge_base_updated": True
        }), 200
        
    except Exception as e:
        logger.error(f"Error answering request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/requests/<request_id>/unresolved', methods=['POST'])
def mark_unresolved(request_id: str):
    """Mark request as unresolved"""
    try:
        if request_id not in help_requests:
            return jsonify({"error": "Request not found"}), 404
        
        req = help_requests[request_id]
        
        if req.status != RequestStatus.PENDING.value:
            return jsonify({"error": f"Request is already {req.status}"}), 400
        
        req.status = RequestStatus.UNRESOLVED.value
        req.resolved_at = datetime.now()
        
        log_action(request_id, "marked_unresolved", "supervisor")
        
        logger.info(f"Request {request_id} marked as unresolved")
        
        return jsonify({
            "status": "success",
            "message": "Request marked as unresolved"
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking unresolved: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge', methods=['GET'])
def query_knowledge():
    """Query knowledge base or list all entries"""
    try:
        query_param = request.args.get('query')
        
        if query_param:
            match = search_knowledge_base(query_param)
            
            if match:
                match_dict = asdict(match)
                match_dict['learned_at'] = match.learned_at.isoformat()
                if match.last_used_at:
                    match_dict['last_used_at'] = match.last_used_at.isoformat()
                
                return jsonify({
                    "found": True,
                    "entry": match_dict
                }), 200
            else:
                return jsonify({
                    "found": False,
                    "message": "No matching entry found"
                }), 200
        else:
            entries = []
            for kb in knowledge_base.values():
                kb_dict = asdict(kb)
                kb_dict['learned_at'] = kb.learned_at.isoformat()
                if kb.last_used_at:
                    kb_dict['last_used_at'] = kb.last_used_at.isoformat()
                entries.append(kb_dict)
            
            entries.sort(key=lambda x: x['usage_count'], reverse=True)
            
            return jsonify({
                "entries": entries,
                "count": len(entries)
            }), 200
        
    except Exception as e:
        logger.error(f"Error querying knowledge: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        check_expired_requests()
        
        pending = sum(1 for r in help_requests.values() if r.status == RequestStatus.PENDING.value)
        resolved = sum(1 for r in help_requests.values() if r.status == RequestStatus.RESOLVED.value)
        unresolved = sum(1 for r in help_requests.values() if r.status == RequestStatus.UNRESOLVED.value)
        expired = sum(1 for r in help_requests.values() if r.status == RequestStatus.EXPIRED.value)
        
        response_times = []
        for req in help_requests.values():
            if req.resolved_at and req.status == RequestStatus.RESOLVED.value:
                delta = (req.resolved_at - req.created_at).total_seconds() / 60
                response_times.append(delta)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return jsonify({
            "requests": {
                "total": len(help_requests),
                "pending": pending,
                "resolved": resolved,
                "unresolved": unresolved,
                "expired": expired
            },
            "knowledge_base": {
                "total_entries": len(knowledge_base),
                "total_usage": sum(kb.usage_count for kb in knowledge_base.values())
            },
            "performance": {
                "avg_response_time_minutes": round(avg_response_time, 2),
                "resolution_rate": round(resolved / len(help_requests) * 100, 2) if help_requests else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Frontdesk HITL API Server")
    logger.info(f"Knowledge base initialized with {len(knowledge_base)} entries")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )