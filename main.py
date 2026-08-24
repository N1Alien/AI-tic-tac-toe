from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

app = FastAPI()

class GameState(BaseModel):
    board: list[str]
    player_symbol: str

# W Codespaces Ollama będzie działać na tym samym serwerze
OLLAMA_URL = "http://127.0.0.1:11434"

@app.post("/api/move")
async def ai_move(state: GameState):
    grid_rows = []
    for i in range(0, 9, 3):
        row_cells = []
        for j in range(i, i + 3):
            if state.board[j] == "":
                row_cells.append(str(j))
            else:
                row_cells.append(state.board[j])
        grid_rows.append(f"Row {i//3 + 1}: " + " | ".join(row_cells))

    board_string_representation = "\n".join(grid_rows)

    prompt = f"""You are a perfect, flawless Tic-Tac-Toe AI engine. You play as 'O'. The opponent plays as 'X'.
Your goal is to NEVER lose and ALWAYS exploit the opponent's mistakes to win.

CURRENT GRID ARCHITECTURE (numbers represent empty, available nodes):
{board_string_representation}

CRITICAL RULES FOR MOVE SELECTION (Follow this exact priority order):
1. WIN IMMEDIATELY: If there is a row, column, or diagonal where you already have TWO 'O' tokens and ONE empty number, select that empty number to WIN right now.
2. BLOCK OPPONENT: If the opponent ('X') has TWO tokens in any line and ONE empty number, you MUST choose that empty number to BLOCK them from winning.
3. FORK / STRATEGY: Take the center node (4) if it is free. If not, prioritize corner nodes (0, 2, 6, 8) to create traps.

Look at the grid, identify all lines, find the single best node according to the rules, and output ONLY that digit (0-8).
No text, no markdown blocks, no thinking logs, no extra characters. Just a single integer."""


    payload = {
        "model": "qwen2.5:0.5b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=15.0)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Ollama offline")

            result = response.json()
            ai_response_text = result.get("response", "").strip()

            if ai_response_text.isdigit():
                chosen_node = int(ai_response_text)
                if chosen_node in range(9) and state.board[chosen_node] == "":
                    return {"move": chosen_node}

            for index, node_value in enumerate(state.board):
                if node_value == "": return {"move": index}

    except Exception:
        for index, node_value in enumerate(state.board):
            if node_value == "": return {"move": index}

@app.get("/")
async def serve_cyberpunk_hud():
    return FileResponse("index.html")
