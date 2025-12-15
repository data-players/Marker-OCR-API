#!/bin/bash
# Script pour tester Marker avec de vrais fichiers PDF
# Utilise docker-compose.test-FullStack.yml avec toutes les dépendances Marker

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Marker avec fichiers PDF réels${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Vérifier que docker-compose.test-FullStack.yml existe
if [ ! -f "docker-compose.test-FullStack.yml" ]; then
    echo -e "${RED}❌ docker-compose.test-FullStack.yml non trouvé${NC}"
    exit 1
fi

# Vérifier que le fichier PDF existe
PDF_FILE="tests/backend/FullStack/file-to-parse/exemple_facture.pdf"
if [ ! -f "$PDF_FILE" ]; then
    echo -e "${YELLOW}⚠ Fichier PDF non trouvé: $PDF_FILE${NC}"
    echo -e "${YELLOW}  Le test utilisera le fichier s'il est monté dans le conteneur${NC}"
fi

echo -e "${BLUE}📄 Fichier à traiter: $PDF_FILE${NC}"
echo ""

# Fonction pour construire l'image
build_image() {
    echo -e "${BLUE}🔧 Construction de l'image de test avec Marker...${NC}"
    echo -e "${YELLOW}   (Cela peut prendre plusieurs minutes la première fois)${NC}"
    docker-compose -f docker-compose.test-FullStack.yml build backend-test-FullStack
    echo -e "${GREEN}✓ Image construite${NC}"
    echo ""
}

# Fonction pour démarrer les services
start_services() {
    echo -e "${BLUE}🚀 Démarrage des services de test...${NC}"
    docker-compose -f docker-compose.test-FullStack.yml up -d
    echo -e "${GREEN}✓ Services démarrés${NC}"
    echo ""
}

# Fonction pour exécuter le test
run_test() {
    echo -e "${BLUE}🧪 Exécution du test Marker avec logs...${NC}"
    echo ""
    
    docker-compose -f docker-compose.test-FullStack.yml exec -T backend-test-FullStack bash -c "
        export MARKER_DEBUG_LOGS=1
        export PYTHONPATH=/app
        cd /app
        python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, '/app')

from app.services.document_parser import DocumentParserService
from app.models.enums import OutputFormat

async def test_marker_logs():
    print('=' * 80)
    print('Testing Marker log capture with real PDF')
    print('=' * 80)
    
    os.environ['MARKER_DEBUG_LOGS'] = '1'
    
    # Try multiple possible paths
    pdf_paths = [
        '/app/../tests/backend/FullStack/file-to-parse/exemple_facture.pdf',
        '/app/tests/backend/FullStack/file-to-parse/exemple_facture.pdf',
        '/app/uploads/exemple_facture.pdf'
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print('❌ PDF file not found in any of these locations:')
        for path in pdf_paths:
            print(f'   - {path}')
        return
    
    print(f'📄 Processing: {pdf_path}')
    print('-' * 80)
    
    sub_steps_seen = []
    marker_logs_seen = []
    
    async def step_callback(step_name: str, status: str, timestamp_or_substep=None):
        if status == 'sub_step':
            if isinstance(timestamp_or_substep, str):
                sub_step_name = timestamp_or_substep
                if sub_step_name not in sub_steps_seen:
                    sub_steps_seen.append(sub_step_name)
                    print(f'✅ Sub-step detected: {sub_step_name}')
            elif isinstance(timestamp_or_substep, tuple):
                sub_step_name, end_time = timestamp_or_substep
                print(f'✅ Sub-step completed: {sub_step_name} (duration: {end_time:.3f}s)')
        else:
            print(f'📊 Step: {step_name} -> {status}')
    
    parser = DocumentParserService()
    
    try:
        result = await parser.parse_document(
            file_path=pdf_path,
            output_format=OutputFormat.MARKDOWN,
            force_ocr=False,
            extract_images=False,
            step_callback=step_callback
        )
        
        print('-' * 80)
        print('✅ Processing completed!')
        print(f'📝 Sub-steps captured: {len(sub_steps_seen)}')
        for i, step in enumerate(sub_steps_seen, 1):
            print(f'  {i}. {step}')
        
        if result.get('markdown'):
            print(f'📄 Markdown length: {len(result[\"markdown\"])} characters')
            print(f'📄 First 300 chars:')
            print(result['markdown'][:300])
            print('...')
        
        print('')
        print('=' * 80)
        print('Test Summary:')
        print(f'  - Sub-steps detected: {len(sub_steps_seen)}')
        print(f'  - Markdown generated: {\"Yes\" if result.get(\"markdown\") else \"No\"}')
        print('=' * 80)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_marker_logs())
PYTHON_SCRIPT
"
}

# Fonction pour ouvrir un shell interactif
open_shell() {
    echo -e "${BLUE}🐚 Ouverture d'un shell interactif...${NC}"
    docker-compose -f docker-compose.test-FullStack.yml exec backend-test-FullStack bash
}

# Fonction pour voir les logs
view_logs() {
    echo -e "${BLUE}📋 Affichage des logs...${NC}"
    docker-compose -f docker-compose.test-FullStack.yml logs -f backend-test-FullStack
}

# Fonction pour arrêter les services
stop_services() {
    echo -e "${BLUE}🛑 Arrêt des services...${NC}"
    docker-compose -f docker-compose.test-FullStack.yml down
    echo -e "${GREEN}✓ Services arrêtés${NC}"
}

# Menu principal
case "${1:-test}" in
    build)
        build_image
        ;;
    start)
        start_services
        ;;
    test)
        build_image
        start_services
        sleep 3  # Attendre que les services soient prêts
        run_test
        ;;
    shell)
        start_services
        open_shell
        ;;
    logs)
        view_logs
        ;;
    stop)
        stop_services
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [build|start|test|shell|logs|stop]${NC}"
        echo ""
        echo "  build  - Construire l'image de test"
        echo "  start  - Démarrer les services"
        echo "  test   - Construire, démarrer et exécuter le test (défaut)"
        echo "  shell  - Ouvrir un shell interactif dans le conteneur"
        echo "  logs   - Voir les logs en temps réel"
        echo "  stop   - Arrêter les services"
        echo ""
        exit 1
        ;;
esac


