#!/bin/bash

# Script pour tester plusieurs playlists Spotify rapidement
# Usage: ./test_playlists.sh

echo "🎵 Test de playlists Spotify pour InstantMusic"
echo "=============================================="
echo ""

# Liste de playlists à tester (ajoutez les vôtres!)
PLAYLISTS=(
    # Playlists Spotify populaires
    "37i9dQZF1DXcBWIGoYBM5M:Today's Top Hits"
    "37i9dQZF1DX0XUsuxWHRQd:RapCaviar"
    "37i9dQZF1DX4o1oenSJRJd:Top Hits 2000s"
    "37i9dQZF1DX4UtSsGT1Sbe:All Out 80s"
    "37i9dQZF1DX1lVhptIYRda:Hot Country"
    
    # Ajoutez vos propres IDs ici:
    # "VOTRE_ID_ICI:Description"
)

WORKING_PLAYLISTS=()
FAILED_PLAYLISTS=()

for entry in "${PLAYLISTS[@]}"; do
    # Séparer l'ID et la description
    IFS=':' read -r id description <<< "$entry"
    
    echo "----------------------------------------"
    echo "Test: $description"
    echo "ID: $id"
    echo ""
    
    # Exécuter le test
    if docker compose exec -T backend python test_playlist_access.py "$id" > /dev/null 2>&1; then
        echo "✅ SUCCÈS: Cette playlist fonctionne!"
        WORKING_PLAYLISTS+=("$id:$description")
    else
        echo "❌ ÉCHEC: Playlist bloquée (403)"
        FAILED_PLAYLISTS+=("$id:$description")
    fi
    echo ""
done

echo "=============================================="
echo "📊 RÉSULTATS FINAUX"
echo "=============================================="
echo ""

if [ ${#WORKING_PLAYLISTS[@]} -gt 0 ]; then
    echo "✅ Playlists ACCESSIBLES (${#WORKING_PLAYLISTS[@]}):"
    for entry in "${WORKING_PLAYLISTS[@]}"; do
        IFS=':' read -r id description <<< "$entry"
        echo "   - $description"
        echo "     ID: $id"
    done
    echo ""
else
    echo "❌ Aucune playlist accessible trouvée"
    echo ""
fi

if [ ${#FAILED_PLAYLISTS[@]} -gt 0 ]; then
    echo "❌ Playlists BLOQUÉES (${#FAILED_PLAYLISTS[@]}):"
    for entry in "${FAILED_PLAYLISTS[@]}"; do
        IFS=':' read -r id description <<< "$entry"
        echo "   - $description"
    done
    echo ""
fi

echo "=============================================="
echo "💡 RECOMMANDATIONS:"
echo ""

if [ ${#WORKING_PLAYLISTS[@]} -gt 0 ]; then
    echo "Vous pouvez utiliser ces IDs dans votre application:"
    for entry in "${WORKING_PLAYLISTS[@]}"; do
        IFS=':' read -r id description <<< "$entry"
        echo "   $id"
    done
else
    echo "1. Créez votre propre playlist publique sur Spotify"
    echo "2. Ajoutez au moins 10 morceaux"
    echo "3. Testez-la avec:"
    echo "   docker compose exec backend python test_playlist_access.py VOTRE_ID"
    echo ""
    echo "OU"
    echo ""
    echo "Implémentez OAuth 2.0 pour un accès complet aux playlists"
    echo "Voir: SPOTIFY_PLAYLISTS.md"
fi

echo "=============================================="
