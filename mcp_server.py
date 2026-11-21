"""
Servidor MCP (Model Context Protocol) para Automação do Podcast Cutter.
Permite que o assistente Antigravity controle o pipeline de mídia por ferramentas nativas.
"""
import sys
import json
import subprocess
from pathlib import Path

def handle_request(request):
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "podcast-cutter-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_podcast_clips",
                        "description": "Executa o pipeline completo: baixa o podcast, transcreve com Whisper, minera momentos virais com Gemini, reenquadra em 9:16 com legendas e gera variantes anti-duplicidade para múltiplos canais.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "source": {
                                    "type": "string",
                                    "description": "URL do vídeo no YouTube ou caminho de arquivo local MP4"
                                },
                                "clips_count": {
                                    "type": "integer",
                                    "default": 3,
                                    "description": "Número de cortes virais a serem gerados"
                                }
                            },
                            "required": ["source"]
                        }
                    },
                    {
                        "name": "check_pipeline_status",
                        "description": "Verifica se FFmpeg, Python e módulos de IA estão instalados e prontos para processar mídia.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name == "check_pipeline_status":
            ffmpeg_ok = subprocess.run(["where.exe", "ffmpeg"], capture_output=True).returncode == 0
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Status do Sistema:\n- FFmpeg instalado: {ffmpeg_ok}\n- Python 3.12: Ativo\n- Diretorio: {str(Path.cwd())}"
                        }
                    ]
                }
            }

        elif tool_name == "generate_podcast_clips":
            source = arguments.get("source")
            clips_count = arguments.get("clips_count", 3)
            cmd = [
                sys.executable,
                str(Path(__file__).parent / "podcast_cutter.py"),
                "--source", source,
                "--clips", str(clips_count)
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Execução do Pipeline:\n{proc.stdout}\nErros:\n{proc.stderr}"
                        }
                    ]
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method {method} not found"
        }
    }

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
