import asyncio
import edge_tts

async def main():
    with open('apresentacao.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    paragraphs = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('---'):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(' '.join(current))

    texto = '\n\n'.join(p for p in paragraphs if p)

    tts = edge_tts.Communicate(texto, voice='pt-BR-AntonioNeural')
    await tts.save('apresentacao.mp3')
    print(f' Audio gerado: apresentacao.mp3')
    print(f' Caracteres: {len(texto)}')

if __name__ == '__main__':
    asyncio.run(main())
