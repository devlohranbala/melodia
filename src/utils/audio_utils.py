"""Audio utilities for device management."""

from typing import List, Dict, Optional

def get_audio_devices() -> List[Dict[str, any]]:
    """Get list of available audio output devices.
    
    Returns:
        List of dictionaries containing device information.
        Each dict has 'id', 'name', and 'is_default' keys.
    """
    devices = []
    
    try:
        # Try using sounddevice first (more reliable)
        import sounddevice as sd
        
        device_list = sd.query_devices()
        default_output = sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else sd.default.device
        
        for i, device in enumerate(device_list):
            # Only include output devices (max_output_channels > 0)
            if device['max_output_channels'] > 0:
                devices.append({
                    'id': i,
                    'name': device['name'],
                    'is_default': i == default_output,
                    'hostapi': device.get('hostapi', 'Unknown')
                })
                
    except ImportError:
        # Fallback to pyaudio if sounddevice is not available
        try:
            import pyaudio
            
            audio = pyaudio.PyAudio()
            info = audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            for i in range(numdevices):
                device_info = audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxOutputChannels', 0) > 0:
                    devices.append({
                        'id': i,
                        'name': device_info.get('name', f'Device {i}'),
                        'is_default': device_info.get('defaultSampleRate', 0) > 0,
                        'hostapi': 'PyAudio'
                    })
            
            audio.terminate()
            
        except ImportError:
            # If neither library is available, provide system default
            devices.append({
                'id': 0,
                'name': 'Sistema Padrão',
                'is_default': True,
                'hostapi': 'System'
            })
    
    except Exception as e:
        # Fallback in case of any error
        print(f"Erro ao obter dispositivos de áudio: {e}")
        devices.append({
            'id': 0,
            'name': 'Sistema Padrão',
            'is_default': True,
            'hostapi': 'System'
        })
    
    return devices

def get_device_name_by_id(device_id: Optional[int]) -> str:
    """Get device name by ID.
    
    Args:
        device_id: Device ID to look up
        
    Returns:
        Device name or 'Sistema Padrão' if not found
    """
    if device_id is None:
        return 'Sistema Padrão'
        
    devices = get_audio_devices()
    for device in devices:
        if device['id'] == device_id:
            return device['name']
    
    return 'Sistema Padrão'

def set_audio_output_device(device_id: Optional[int]) -> bool:
    """Set the audio output device.
    
    Args:
        device_id: Device ID to set as output, None for system default
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try using sounddevice
        import sounddevice as sd
        
        if device_id is None:
            # Reset to system default
            sd.default.device = None
        else:
            # Set specific device
            sd.default.device = (None, device_id)  # (input, output)
        
        return True
        
    except ImportError:
        # sounddevice not available, return True as fallback
        # (pyglet will use system default)
        return True
        
    except Exception as e:
        print(f"Erro ao definir dispositivo de áudio: {e}")
        return False