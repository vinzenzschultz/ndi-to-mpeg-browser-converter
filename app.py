import cv2
import numpy as np
import NDIlib as ndi
from flask import Flask, Response, render_template, request, jsonify
import time

app = Flask(__name__)

if not ndi.initialize():
    raise RuntimeError("NDI konnte nicht initialisiert werden")

def get_ndi_sources():
    find = ndi.find_create_v2()
    ndi.find_wait_for_sources(find, 5000)
    sources = ndi.find_get_current_sources(find)
    return sources


@app.route('/')
def index():
    sources = get_ndi_sources()
    return render_template('index.html', sources=sources)


def ndi_receiver(source, is_ip=False):
    if not ndi.initialize():
        raise RuntimeError("NDI konnte nicht initialisiert werden")

    recv_create = ndi.RecvCreateV3()
    recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
    recv = ndi.recv_create_v3(recv_create)

    if recv is None:
        raise RuntimeError("NDI Empfänger konnte nicht erstellt werden")

    print(f"warte auf NDI Quelle: {source}")

    while True:
        try:
            if is_ip:
                ndi.recv_connect(recv, f"NDI Quelle: {source}")
                print(f"verbunden mit NDI IP: {source}")
                break

            sources = get_ndi_sources()
            selected_source = next((src for src in sources if src.ndi_name == source), None)

            if selected_source:
                ndi.recv_connect(recv, selected_source)
                print(f"verbunden mit NDI Quelle: {source}")
                break
            else:
                print(f"NDI Quelle '{source}' nicht gefunden")
                time.sleep(3)

        except Exception as e:
            print(f"Fehler beim Verbinden: {e}")
            time.sleep(3)

    last_valid_frame = None

    while True:
        try:
            frame_type, video_data, _, _ = ndi.recv_capture_v2(recv, 5000)

            if frame_type == ndi.FRAME_TYPE_VIDEO:
                frame = np.frombuffer(video_data.data, dtype=np.uint8)
                frame = frame.reshape((video_data.yres, video_data.xres, 4))
                last_valid_frame = frame
                
                ndi.recv_free_video_v2(recv, video_data)

            elif last_valid_frame is not None:
                #print("kein neuen Frame erhalten")
                pass

            else:
                #print("kein Frame vorhanden")
                time.sleep(0.1)
                continue

            _, jpeg = cv2.imencode('.jpg', last_valid_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        except Exception as e:
            print(f"Fehler während der Stream Verarbeitung: {e}")
            time.sleep(1)


@app.route('/stream')
def stream():
    sources = get_ndi_sources()
    stream_param = request.args.get('source', default="0")  #Standardwert = 0
    ip_param = request.args.get('ip')

    if ip_param:
        return Response(ndi_receiver(ip_param, is_ip=True), mimetype='multipart/x-mixed-replace; boundary=frame')

    try:
        stream_index = int(stream_param)
        
        if 0 <= stream_index < len(sources):
            stream_name = sources[stream_index].ndi_name
        else:
            return "Stream-Index ungültig", 400
    except ValueError:
        stream_name = stream_param if any(src.ndi_name == stream_param for src in sources) else sources[0].ndi_name

    return Response(ndi_receiver(stream_name), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/sources')
def sources():
    sources = get_ndi_sources()
    
    source_list = []
    for src in sources:
        source_list.append({
            "name": src.ndi_name,
            "ip": src.p_ndi_address if hasattr(src, 'p_ndi_address') else "Unbekannt"
        })

    return jsonify(source_list)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
