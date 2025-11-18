EditorPDF/
│   abrir_editor.vbs        -> Script responsável por iniciar o programa de forma silenciosa,
│                              evitando a exibição de janelas de terminal durante a execução.
│
│   installer.bat           -> Instalador principal do sistema. Ele configura bibliotecas,
│                              registra atalhos, cria o atalho de teclado (CTRL+ALT+P) e
│                              prepara o ambiente necessário para o funcionamento do EditorPDF.
│
│   logoSerenaLove.ico      -> Ícone oficial do sistema. Previsto para uso futuro na criação
│                              de atalhos e na identificação visual do aplicativo.
│
├───assets
│   ├───AutoHotkey/         -> Versão portátil do AutoHotkey utilizada pelo sistema.
│   │                          Não requer instalação e é usada apenas para registrar atalhos
│   │                          personalizados, como o CTRL+ALT+P.
│   │
│   ├───icons/              -> Conjunto de arquivos SVG utilizados como ícones dentro da
│   │                          interface gráfica do programa.
│   │
│   │   atalho.ahk          -> Script para criação do atalho de teclado que inicia o aplicativo.
│   │
│   │   start_serena.vbs    -> Script auxiliar para iniciar o EditorPDF de maneira silenciosa
│   │                          a partir do AutoHotkey ou do instalador.
│   │
│   │   tema_escuro.qss     -> Arquivo de estilo (stylesheet) utilizado para aplicar o tema
│   │                          escuro à interface gráfica do aplicativo.
│
└───src
        main.py             -> Arquivo principal do sistema. Realiza a inicialização da
        │                      aplicação, configura a interface e coordena os módulos internos.
        │
        pdf_viewer.py       -> Módulo responsável pela visualização de arquivos PDF dentro
        │                      do programa, incluindo navegação, renderização e zoom.
        │
        geradorDocumentos.py -> Componente encarregado da geração de novos documentos,
        │                       exportação de PDFs e criação de relatórios automáticos.
        │
        conversor.py        -> Módulo dedicado à conversão de arquivos entre formatos,
        │                      como PDF, imagens ou outros tipos compatíveis.
        │
        logicaPagina.py     -> Controla a lógica de funcionamento das páginas e seções da
        │                      interface, incluindo comportamentos de botões e janelas.
        │
        globais.py          -> Armazena variáveis globais e configurações compartilhadas
        │                      entre os módulos do sistema.
        │
        signals.py          -> Gerencia a comunicação interna através de sinais e eventos,
                               coordenando a interação entre os componentes da interface.




Instruções de Instalação e Configuração

Para garantir o funcionamento adequado do programa, é necessário executar o arquivo installer.bat incluído no pacote. Este instalador realiza automaticamente todas as etapas essenciais para a preparação do ambiente, incluindo:

Instalação das bibliotecas necessárias para a execução do aplicativo;

Configuração dos atalhos de sistema, incluindo o atalho na área de trabalho;

Criação de um atalho de teclado, permitindo abrir o programa diretamente através da combinação:

CTRL + ALT + P

A execução do instalador é obrigatória na primeira utilização, pois sem essa etapa o programa não terá acesso às dependências necessárias e os atalhos não serão configurados corretamente.

Após a conclusão da instalação, o software estará pronto para uso imediato.