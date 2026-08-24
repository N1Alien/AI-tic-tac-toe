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

    prompt = f"""You are playing Tic-Tac-Toe. Your symbol is 'O' and the opponent is 'X'.
Current grid structure (numbers represent empty, available nodes):
{board_string_representation}

Choose the best empty node to win or block.
Output ONLY the single digit (0 to 8) representing your move. Do not write text, just the number."""

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
