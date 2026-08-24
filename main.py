from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

app = FastAPI()

class GameState(BaseModel):
    board: list[str]
    player_symbol: str

OLLAMA_URL = "http://127.0.0.1:11434"

def check_winner(b):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for line in lines:
        if b[line[0]] == b[line[1]] == b[line[2]] and b[line[0]] != "":
            return b[line[0]]
    if "" not in b:
        return "Draw"
    return None

def minimax(b, depth, is_maximizing):
    score = check_winner(b)
    if score == "O": return 10 - depth
    if score == "X": return depth - 10
    if score == "Draw": return 0

    if is_maximizing:
        best_score = -float('inf')
        for i in range(9):
            if b[i] == "":
                b[i] = "O"
                sim_score = minimax(b, depth + 1, False)
                b[i] = ""
                best_score = max(sim_score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for i in range(9):
            if b[i] == "":
                b[i] = "X"
                sim_score = minimax(b, depth + 1, True)
                b[i] = ""
                best_score = min(sim_score, best_score)
        return best_score

def find_best_move(b):
    best_score = -float('inf')
    move = -1
    for i in range(9):
        if b[i] == "":
            b[i] = "O"
            move_score = minimax(b, 0, False)
            b[i] = ""
            if move_score > best_score:
                best_score = move_score
                move = i
    return move

@app.post("/api/move")
async def ai_move(state: GameState):
    perfect_move = find_best_move(state.board)
    ai_comment = "INJECTING CORRUPTION..."
    prompt = f"Write one short tactical cyberpunk phrase (max 5 words) about rogue AI attacking slot {perfect_move}. Output ONLY the phrase, no intro, no comments."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate", 
                json={"model": "qwen2.5:0.5b", "prompt": prompt, "stream": False, "options": {"temperature": 0.7}},
                timeout=5.0
            )
            if response.status_code == 200:
                ai_comment = response.json().get("response", "").strip().replace('"', '')
    except Exception:
        pass

    return {"move": perfect_move, "comment": ai_comment}

@app.get("/")
async def serve_cyberpunk_hud():
    return FileResponse("index.html")
