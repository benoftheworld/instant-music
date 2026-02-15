#!/usr/bin/env python
"""
Script pour tester l'accessibilité d'une playlist Spotify.
Usage: python test_playlist_access.py <playlist_id_or_url>
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.playlists.services import spotify_service

def extract_playlist_id(input_str):
    """Extrait l'ID de playlist depuis une URL ou un ID direct."""
    if 'spotify.com/playlist/' in input_str:
        # Format: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...
        return input_str.split('playlist/')[1].split('?')[0]
    return input_str

def test_playlist(playlist_id):
    """Teste l'accessibilité d'une playlist."""
    print(f"🔍 Test de la playlist: {playlist_id}")
    print("-" * 60)
    
    try:
        # 1. Récupérer les détails de la playlist
        print("📋 Étape 1: Récupération des informations...")
        details = spotify_service.get_playlist(playlist_id)
        
        if not details:
            print("❌ Impossible de récupérer les informations de la playlist")
            return False
        
        print(f"✅ Nom: {details.get('name', 'N/A')}")
        print(f"✅ Propriétaire: {details.get('owner', {}).get('display_name', 'N/A')}")
        print(f"✅ Public: {details.get('public', 'N/A')}")
        print(f"✅ Nombre de tracks (déclaré): {details.get('tracks', {}).get('total', 0)}")
        
        # 2. Essayer de récupérer les tracks
        print("\n🎵 Étape 2: Récupération des morceaux...")
        tracks = spotify_service.get_playlist_tracks(playlist_id)
        
        if not tracks:
            print("❌ ERREUR: Impossible de récupérer les morceaux (probablement 403 Forbidden)")
            print("⚠️  Cette playlist n'est PAS accessible avec Client Credentials Flow")
            return False
        
        print(f"✅ {len(tracks)} morceaux récupérés avec succès!")
        
        # 3. Vérifier que c'est suffisant pour le jeu
        if len(tracks) >= 4:
            print(f"\n🎮 Cette playlist est UTILISABLE pour le jeu!")
            print(f"   Morceaux disponibles: {len(tracks)}")
            print(f"   Minimum requis: 4")
            
            # Afficher quelques exemples
            print(f"\n📝 Exemples de morceaux:")
            for i, track in enumerate(tracks[:5], 1):
                print(f"   {i}. {track.get('name')} - {', '.join(track.get('artists', []))}")
            
            return True
        else:
            print(f"\n⚠️  Playlist trop petite: {len(tracks)} morceaux (minimum 4 requis)")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        print("⚠️  Cette playlist n'est PAS accessible")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_playlist_access.py <playlist_id_or_url>")
        print("\nExemples:")
        print("  python test_playlist_access.py 37i9dQZF1DXcBWIGoYBM5M")
        print("  python test_playlist_access.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        sys.exit(1)
    
    input_str = sys.argv[1]
    playlist_id = extract_playlist_id(input_str)
    
    result = test_playlist(playlist_id)
    
    print("\n" + "=" * 60)
    if result:
        print("✅ RÉSULTAT: Playlist ACCESSIBLE et UTILISABLE")
        print(f"   Vous pouvez utiliser l'ID: {playlist_id}")
    else:
        print("❌ RÉSULTAT: Playlist NON ACCESSIBLE")
        print("   Essayez une autre playlist")
    print("=" * 60)
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
