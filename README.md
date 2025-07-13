# 🎵 Melodia - Modern Music Player

Um player de música moderno e elegante com interface gráfica intuitiva e API REST integrada. O Melodia combina uma experiência de usuário rica com funcionalidades avançadas de gerenciamento de música.

## ✨ Características Principais

### 🎨 Interface Moderna
- Interface gráfica elegante com tema escuro
- Design responsivo e intuitivo
- Controles de reprodução modernos
- Visualização de thumbnails e metadados

### 🎵 Funcionalidades de Reprodução
- Reprodução de arquivos de áudio locais
- Controle de volume com slider
- Barra de progresso interativa
- Navegação entre faixas (anterior/próxima)
- Suporte a playlists personalizadas

### 🔍 Busca e Download
- Busca de música online
- Download automático de áudio via yt-dlp
- Busca local por título e artista
- Gerenciamento de biblioteca musical

### 📋 Gerenciamento de Playlists
- Criação de playlists personalizadas
- Adição/remoção de músicas
- Organização por categorias
- Reprodução de playlists completas

### 🌐 API REST
- API FastAPI completa
- Endpoints para todas as funcionalidades
- Documentação automática (Swagger)
- Suporte a CORS para integração web

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica**: CustomTkinter
- **API Backend**: FastAPI + Uvicorn
- **Download de Áudio**: yt-dlp
- **Reprodução de Áudio**: pyglet + sounddevice
- **Processamento de Imagens**: Pillow
- **HTTP Client**: aiohttp + requests

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Sistema operacional: Windows, macOS ou Linux

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd melodia
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o aplicativo**
   ```bash
   python main.py
   ```

## 🚀 Como Usar

### Iniciando o Aplicativo

Ao executar `python main.py`, o Melodia irá:
1. Iniciar o servidor API em `http://127.0.0.1:8000`
2. Abrir a interface gráfica
3. Criar automaticamente a pasta `~/melodia` para downloads

### Navegação Principal

A interface possui uma barra lateral com as seguintes seções:
- **Feed**: Visualização de todas as músicas
- **Busca**: Pesquisa online e local
- **Playlists**: Gerenciamento de playlists
- **Configurações**: Ajustes do aplicativo

### Funcionalidades Principais

#### 🎵 Reprodução de Música
- Clique duplo em uma música para reproduzir
- Use os controles na parte inferior: ⏮ ▶/⏸ ⏭
- Ajuste o volume com o slider
- Navegue pela música com a barra de progresso

#### 🔍 Busca e Download
1. Acesse a seção "Busca"
2. Digite o nome da música ou artista
3. Clique em "Buscar" para pesquisar online
4. Clique no botão de download ao lado do resultado desejado
5. A música será baixada automaticamente para sua biblioteca

#### 📋 Gerenciamento de Playlists
1. Acesse a seção "Playlists"
2. Clique em "Nova Playlist" para criar
3. Arraste músicas para adicionar à playlist
4. Clique com botão direito para opções adicionais

## 🌐 API REST

O Melodia inclui uma API REST completa que permite integração com outras aplicações.

### Documentação da API

Acesse `http://127.0.0.1:8000/docs` para ver a documentação interativa (Swagger UI).

### Principais Endpoints

#### Músicas
- `GET /api/songs` - Listar todas as músicas
- `GET /api/songs/{song_id}` - Obter música específica
- `DELETE /api/songs/{song_id}` - Excluir música
- `GET /api/songs/{song_id}/file` - Download do arquivo de áudio

#### Playlists
- `GET /api/playlists` - Listar playlists
- `POST /api/playlists` - Criar nova playlist
- `POST /api/playlists/{name}/songs` - Adicionar música à playlist

#### Busca e Download
- `GET /api/search?query={termo}` - Buscar música online
- `POST /api/download` - Iniciar download de música

#### Configurações
- `GET /api/settings` - Obter configurações
- `PUT /api/settings` - Atualizar configurações

## 📁 Estrutura do Projeto

```
melodia/
├── main.py                 # Ponto de entrada principal
├── requirements.txt        # Dependências do projeto
├── src/
│   ├── api/               # API REST (FastAPI)
│   │   ├── main.py        # Configuração da API
│   │   ├── models.py      # Modelos de dados da API
│   │   ├── services.py    # Serviços da API
│   │   └── client.py      # Cliente HTTP para API
│   ├── controllers/       # Controladores da aplicação
│   │   ├── player_controller.py
│   │   ├── search_controller.py
│   │   ├── playlist_controller.py
│   │   └── ...
│   ├── core/             # Núcleo da aplicação
│   │   ├── player.py     # Engine de reprodução
│   │   ├── events.py     # Sistema de eventos
│   │   └── app_context.py
│   ├── services/         # Serviços de negócio
│   ├── models/           # Modelos de dados
│   ├── ui/              # Componentes de interface
│   ├── managers/        # Gerenciadores de dados
│   └── utils/           # Utilitários
```

## ⚙️ Configurações

### Diretório de Downloads
Por padrão, as músicas são salvas em `~/melodia/`. Este diretório é criado automaticamente.

### Configurações da API
- **Host**: 127.0.0.1
- **Porta**: 8000
- **Documentação**: http://127.0.0.1:8000/docs

### Formatos Suportados
- Áudio: MP3, WAV, FLAC, OGG, M4A
- Imagens: JPG, PNG, WEBP (para thumbnails)

## 🔧 Desenvolvimento

### Arquitetura

O Melodia segue uma arquitetura modular com separação clara de responsabilidades:

- **Controllers**: Gerenciam a lógica de interface e interações
- **Services**: Implementam regras de negócio
- **Models**: Definem estruturas de dados
- **API**: Fornece interface REST para todas as funcionalidades
- **Core**: Contém funcionalidades essenciais (player, eventos)

### Padrões Utilizados
- **MVC**: Separação entre Model, View e Controller
- **Observer**: Sistema de eventos para comunicação entre componentes
- **Factory**: Criação de componentes de UI
- **Dependency Injection**: Contexto da aplicação compartilhado

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🐛 Problemas Conhecidos

- Downloads muito grandes podem demorar para aparecer na interface
- A busca online depende da disponibilidade dos serviços externos

## 📞 Suporte

Se encontrar problemas ou tiver sugestões:
1. Verifique se todas as dependências estão instaladas
2. Consulte a documentação da API em `/docs`
3. Abra uma issue no repositório do projeto

---

**Melodia** - Sua experiência musical moderna e intuitiva! 🎵