from database import SessionLocal, engine
import models

# 1. HARD RESET: Drop all tables and recreate them to ensure clean IDs
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("--- SEEDING 2BOS LIBRARY ---")

# ==============================================================================
# HELPER FUNCTION TO ADD PROJECTS
# ==============================================================================
def create_project(title, diff, desc, solution_context, steps_data):
    # Create Project
    proj = models.Project(
        title=title,
        difficulty=diff,
        description=desc,
        full_solution_context=solution_context
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    
    # Create Steps
    for idx, step in enumerate(steps_data, 1):
        s = models.ProjectStep(
            project_id=proj.id,
            step_order=idx,
            title=step["title"],
            required_concept=step["concept"],
            unlock_code=step["code"]
        )
        db.add(s)
    db.commit()
    print(f"Created: {title}")

# ==============================================================================
# PROJECT 1: MUSIC STREAMING QUEUE (Linked List)
# ==============================================================================
create_project(
    title="Music Streaming Queue",
    diff="Beginner",
    desc="Build the backend for a music player. Manage a playlist where songs are played in order, and users can add songs to the end dynamically.",
    solution_context="Singly Linked List with Head and Tail pointers.",
    steps_data=[
        {
            "title": "The Song Node",
            "concept": "Define a Class for the Node containing Title, Artist, and Next pointer.",
            "code": """class SongNode:
    def __init__(self, title, artist):
        self.title = title
        self.artist = artist
        self.next = None

    def __repr__(self):
        return f"Song({self.title})" """
        },
        {
            "title": "Queue Initialization",
            "concept": "Define the Queue class with Head and Tail pointers.",
            "code": """class MusicQueue:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0"""
        },
        {
            "title": "Enqueue (Add Song)",
            "concept": "Logic: Create node. If empty, head=tail=node. Else, tail.next=node and update tail.",
            "code": """    def add_song(self, title, artist):
        new_song = SongNode(title, artist)
        if self.head is None:
            self.head = new_song
            self.tail = new_song
        else:
            self.tail.next = new_song
            self.tail = new_song
        self.size += 1
        print(f"Added: {title}")"""
        },
        {
            "title": "Play Next",
            "concept": "Logic: Save head data. Move head to head.next. Handle empty list case.",
            "code": """    def play_next(self):
        if self.head is None:
            return "Queue Empty"
        
        current_song = self.head
        self.head = self.head.next
        
        if self.head is None:
            self.tail = None
            
        self.size -= 1
        return f"Playing: {current_song.title}" """
        }
    ]
)

# ==============================================================================
# PROJECT 2: UNDO/REDO TEXT EDITOR (Stacks)
# ==============================================================================
create_project(
    title="Undo/Redo Text Editor",
    diff="Beginner",
    desc="Build the logic for a text editor that supports unlimited Undo and Redo operations.",
    solution_context="Two Stacks approach. One stack for History, one for Future (Redo).",
    steps_data=[
        {
            "title": "Action Class",
            "concept": "Define a class to represent a single edit action (text content).",
            "code": """class Action:
    def __init__(self, text):
        self.text = text
        
    def __repr__(self):
        return f"Action('{self.text}')" """
        },
        {
            "title": "Editor Initialization",
            "concept": "Define Editor class with two lists/stacks: history and future (redo).",
            "code": """class TextEditor:
    def __init__(self):
        self.history = [] # The Undo Stack
        self.future = []  # The Redo Stack
        self.current_text = "" """
        },
        {
            "title": "Write & Undo Logic",
            "concept": "Write: Clear redo stack, push current to history. Undo: Pop history, push to redo.",
            "code": """    def write(self, new_text):
        self.history.append(self.current_text)
        self.future = [] # Clear redo on new action
        self.current_text = new_text

    def undo(self):
        if not self.history:
            return "Nothing to undo"
        
        self.future.append(self.current_text)
        self.current_text = self.history.pop()
        return self.current_text"""
        },
        {
            "title": "Redo Logic",
            "concept": "Redo: Pop from future stack, push current to history, update text.",
            "code": """    def redo(self):
        if not self.future:
            return "Nothing to redo"
            
        self.history.append(self.current_text)
        self.current_text = self.future.pop()
        return self.current_text"""
        }
    ]
)

# ==============================================================================
# PROJECT 3: TINYURL SHORTENER (Hashing/Arrays)
# ==============================================================================
create_project(
    title="TinyURL Shortener",
    diff="Beginner",
    desc="Create a service that converts long URLs into short 6-character codes and back.",
    solution_context="Database ID to Base62 Encoding. Map Integer ID to characters [a-zA-Z0-9].",
    steps_data=[
        {
            "title": "Storage Design",
            "concept": "Use a Dictionary/Map to store ID -> LongURL mapping.",
            "code": """class URLShortener:
    def __init__(self):
        self.id_counter = 1000000 # Start high for 6 chars
        self.url_map = {}
        # Characters for Base62
        self.chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" """
        },
        {
            "title": "Encoding Algorithm",
            "concept": "Logic: Convert Integer ID to Base62 String using modulo and division loop.",
            "code": """    def _id_to_short(self, _id):
        short_url = []
        while _id > 0:
            val = _id % 62
            short_url.append(self.chars[val])
            _id = _id // 62
        return "".join(short_url[::-1])"""
        },
        {
            "title": "Shorten & Restore",
            "concept": "Public methods to save URL, generate ID, and retrieve URL by ID.",
            "code": """    def shorten(self, original_url):
        _id = self.id_counter
        self.id_counter += 1
        
        self.url_map[_id] = original_url
        return f"http://tiny.url/{self._id_to_short(_id)}"

    # Note: Real restoration requires decoding Base62 back to ID,
    # but for this MVP we can just lookup if we knew the ID.
    # (Or implement _short_to_id logic)."""
        }
    ]
)

# ==============================================================================
# PROJECT 4: SOCIAL NETWORK (Graph BFS)
# ==============================================================================
create_project(
    title="Social Network Friends",
    diff="Intermediate",
    desc="Build a friend recommendation system. If A follows B, and B follows C, suggest C to A.",
    solution_context="Graph Adjacency List + Breadth-First Search (BFS).",
    steps_data=[
        {
            "title": "User Node",
            "concept": "Class User with ID and a Set/List of friends.",
            "code": """class User:
    def __init__(self, id):
        self.id = id
        self.friends = set()
        
    def add_friend(self, user):
        self.friends.add(user)"""
        },
        {
            "title": "Recommendation Logic (BFS)",
            "concept": "Use a Queue for BFS. Track 'visited' set. Find friends of friends (Level 2).",
            "code": """    def get_recommendations(self, target_user):
        recommendations = set()
        queue = [target_user]
        visited = {target_user}
        
        # Simple BFS (Depth 2)
        for _ in range(2): # Look 2 layers deep
            level_size = len(queue)
            for _ in range(level_size):
                current = queue.pop(0)
                for friend in current.friends:
                    if friend not in visited:
                        visited.add(friend)
                        queue.append(friend)
                        # Add to results if not direct friend
                        if friend not in target_user.friends:
                            recommendations.add(friend)
                            
        return [u.id for u in recommendations]"""
        }
    ]
)

# ==============================================================================
# PROJECT 5: TYPEAHEAD AUTOCOMPLETE (Trie)
# ==============================================================================
create_project(
    title="Typeahead Autocomplete",
    diff="Intermediate",
    desc="Build a search engine that suggests words as you type.",
    solution_context="Trie (Prefix Tree). Nodes are characters.",
    steps_data=[
        {
            "title": "Trie Node",
            "concept": "Node contains a Dictionary of children and an is_end_of_word boolean.",
            "code": """class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False"""
        },
        {
            "title": "Insert Word",
            "concept": "Loop through characters. Create child node if not exists. Mark end.",
            "code": """class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True"""
        },
        {
            "title": "Search Prefix",
            "concept": "Traverse tree with prefix. If path exists, collect all words below that node.",
            "code": """    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self._collect_words(node, prefix)
        
    def _collect_words(self, node, prefix):
        words = []
        if node.is_end_of_word:
            words.append(prefix)
        for char, child in node.children.items():
            words.extend(self._collect_words(child, prefix + char))
        return words"""
        }
    ]
)

# ==============================================================================
# PROJECT 6: VIRTUAL FILE SYSTEM (N-ary Tree)
# ==============================================================================
create_project(
    title="Virtual File System",
    diff="Intermediate",
    desc="Create an in-memory file explorer (ls, mkdir, cd).",
    solution_context="N-ary Tree. Directories contain a map of children.",
    steps_data=[
        {
            "title": "Directory Node",
            "concept": "Class Directory with name and dictionary of children.",
            "code": """class Directory:
    def __init__(self, name):
        self.name = name
        self.children = {} # Map name -> Directory object"""
        },
        {
            "title": "File System & Mkdir",
            "concept": "Class FileSystem with root. Mkdir adds entry to current directory's children.",
            "code": """class FileSystem:
    def __init__(self):
        self.root = Directory("/")
        self.current = self.root

    def mkdir(self, name):
        if name not in self.current.children:
            self.current.children[name] = Directory(name)
        else:
            print("Directory already exists")"""
        },
        {
            "title": "Change Directory (cd)",
            "concept": "Update 'current' pointer to the child node matching the name.",
            "code": """    def cd(self, name):
        if name == "..":
            # Need parent pointer logic for real implementation
            pass 
        elif name in self.current.children:
            self.current = self.current.children[name]
        else:
            print("Directory not found")"""
        }
    ]
)

# ==============================================================================
# PROJECT 7: STOCK ORDER BOOK (Heaps)
# ==============================================================================
create_project(
    title="Stock Trading Order Book",
    diff="Advanced",
    desc="Build a matching engine for a stock exchange.",
    solution_context="Two Priority Queues: Max-Heap for Buy Orders, Min-Heap for Sell Orders.",
    steps_data=[
        {
            "title": "Order Class",
            "concept": "Class Order with price, quantity, and comparison operators (__lt__) for the Heap.",
            "code": """import heapq

class Order:
    def __init__(self, price, quantity, is_buy):
        self.price = price
        self.quantity = quantity
        self.is_buy = is_buy

    # Heapq uses < operator. 
    # For Buy (Max Heap), we invert logic or store negative price.
    def __lt__(self, other):
        if self.is_buy:
            return self.price > other.price # Highest buy first
        return self.price < other.price # Lowest sell first"""
        },
        {
            "title": "Engine Initialization",
            "concept": "Two lists: buy_heap and sell_heap. Use heapq to push/pop.",
            "code": """class OrderBook:
    def __init__(self):
        self.buy_heap = []
        self.sell_heap = []

    def add_order(self, price, qty, is_buy):
        order = Order(price, qty, is_buy)
        if is_buy:
            heapq.heappush(self.buy_heap, order)
        else:
            heapq.heappush(self.sell_heap, order)"""
        },
        {
            "title": "Matching Engine",
            "concept": "While loops: Check if Top Buy >= Top Sell. If yes, execute trade and reduce quantities.",
            "code": """    def match_orders(self):
        while self.buy_heap and self.sell_heap:
            buy = self.buy_heap[0]
            sell = self.sell_heap[0]

            if buy.price >= sell.price:
                # Trade happens
                trade_qty = min(buy.quantity, sell.quantity)
                print(f"Trade: {trade_qty} @ {sell.price}")
                
                buy.quantity -= trade_qty
                sell.quantity -= trade_qty
                
                if buy.quantity == 0: heapq.heappop(self.buy_heap)
                if sell.quantity == 0: heapq.heappop(self.sell_heap)
            else:
                break # No more matches possible"""
        }
    ]
)

# ==============================================================================
# PROJECT 8: LRU CACHE (HashMap + Doubly LL)
# ==============================================================================
create_project(
    title="High-Speed LRU Cache",
    diff="Advanced",
    desc="Build a cache that evicts the least recently used item when full.",
    solution_context="Combination of HashMap (O(1) lookup) and Doubly Linked List (O(1) removal/move).",
    steps_data=[
        {
            "title": "Doubly Linked Node",
            "concept": "Node with Key, Value, Prev, and Next pointers.",
            "code": """class DNode:
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None"""
        },
        {
            "title": "Cache Structure",
            "concept": "Map for lookups. Dummy head and Dummy tail nodes to simplify edge cases.",
            "code": """class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache_map = {} # Key -> Node
        
        # Dummy Sentinels
        self.head = DNode(0, 0) 
        self.tail = DNode(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head"""
        },
        {
            "title": "Internal Utilities",
            "concept": "Helper methods: _remove(node) and _add_to_front(node).",
            "code": """    def _remove(self, node):
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev

    def _add_to_front(self, node):
        # Add right after dummy head
        nxt = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = nxt
        nxt.prev = node"""
        },
        {
            "title": "Get and Put",
            "concept": "Get: Move to front. Put: Add to front. If full, remove tail.prev.",
            "code": """    def get(self, key):
        if key in self.cache_map:
            node = self.cache_map[key]
            self._remove(node)
            self._add_to_front(node)
            return node.val
        return -1

    def put(self, key, value):
        if key in self.cache_map:
            self._remove(self.cache_map[key])
        
        new_node = DNode(key, value)
        self._add_to_front(new_node)
        self.cache_map[key] = new_node
        
        if len(self.cache_map) > self.capacity:
            # Evict LRU (node before tail)
            lru = self.tail.prev
            self._remove(lru)
            del self.cache_map[lru.key]"""
        }
    ]
)

# ==============================================================================
# PROJECT 9: UBER ROUTE OPTIMIZER (Dijkstra)
# ==============================================================================
create_project(
    title="Uber Route Optimizer",
    diff="Advanced",
    desc="Find shortest path between locations.",
    solution_context="Weighted Graph + Dijkstra Algorithm.",
    steps_data=[
        {
            "title": "Graph Setup",
            "concept": "Adjacency List where edges have weights (distance).",
            "code": """class CityMap:
    def __init__(self):
        self.adj = {}

    def add_road(self, u, v, dist):
        if u not in self.adj: self.adj[u] = []
        if v not in self.adj: self.adj[v] = []
        self.adj[u].append((v, dist))
        self.adj[v].append((u, dist)) # Undirected"""
        },
        {
            "title": "Dijkstra's Algo",
            "concept": "Priority Queue to track shortest distance found so far.",
            "code": """    import heapq

    def shortest_path(self, start, end):
        # (distance, node)
        pq = [(0, start)]
        distances = {start: 0}
        visited = set()

        while pq:
            d, u = heapq.heappop(pq)
            
            if u in visited: continue
            visited.add(u)
            
            if u == end: return d
            
            if u in self.adj:
                for v, weight in self.adj[u]:
                    if v not in visited:
                        new_dist = d + weight
                        if new_dist < distances.get(v, float('inf')):
                            distances[v] = new_dist
                            heapq.heappush(pq, (new_dist, v))
        return -1"""
        }
    ]
)

# ==============================================================================
# PROJECT 10: FILE COMPRESSION (Huffman)
# ==============================================================================
create_project(
    title="File Compression Tool",
    diff="Advanced",
    desc="Compress text using Huffman Coding.",
    solution_context="Frequency Map -> Priority Queue -> Huffman Tree.",
    steps_data=[
        {
            "title": "Frequency Map",
            "concept": "Count occurrences of each character.",
            "code": """from collections import Counter
def get_frequencies(text):
    return Counter(text)"""
        },
        {
            "title": "Huffman Tree",
            "concept": "Node class. Heap logic: Pop two smallest, combine, push back.",
            "code": """import heapq

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
        
    def __lt__(self, other):
        return self.freq < other.freq

def build_tree(text):
    freqs = Counter(text)
    heap = [Node(char, freq) for char, freq in freqs.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        
        heapq.heappush(heap, merged)
        
    return heap[0] # Root"""
        }
    ]
)

db.close()
print("SUCCESS: 2BOS Library Fully Populated.")