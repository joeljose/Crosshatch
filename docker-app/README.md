# Crosshatch Docker API

Dockerized REST API for creating crosshatch artistic effects on portrait images.

## Features

- 🐳 **Easy deployment** with Docker & Docker Compose
- 🚀 **REST API** for programmatic access
- 🎨 **Two styles**: Horizontal and Vortex hatching
- ⚡ **GPU support** for fast processing
- 💻 **CPU fallback** for environments without GPU
- 🔄 **Auto-scaling ready** for production deployments

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- For GPU version: NVIDIA GPU with Docker GPU support

### Option 1: Docker Compose (Recommended)

**For GPU:**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**For CPU:**
```bash
# Build and start
docker-compose -f docker-compose.cpu.yml up -d

# View logs
docker-compose -f docker-compose.cpu.yml logs -f

# Stop
docker-compose -f docker-compose.cpu.yml down
```

### Option 2: Docker Build & Run

**GPU Version:**
```bash
# Build
docker build -t crosshatch:2.0-gpu .

# Run
docker run -d \
  --name crosshatch-api \
  --gpus all \
  -p 5000:5000 \
  -e DEVICE=cuda \
  -e SAM2_MODEL=small \
  crosshatch:2.0-gpu
```

**CPU Version:**
```bash
# Build
docker build -f Dockerfile.cpu -t crosshatch:2.0-cpu .

# Run
docker run -d \
  --name crosshatch-api \
  -p 5000:5000 \
  -e DEVICE=cpu \
  -e SAM2_MODEL=tiny \
  crosshatch:2.0-cpu
```

## API Usage

### Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "crosshatch-api",
  "version": "2.0.0"
}
```

### Create Crosshatch Effect

```bash
# Basic usage
curl -X POST \
  -F "file=@portrait.jpg" \
  http://localhost:5000/api/crosshatch \
  -o output.jpg

# With style option
curl -X POST \
  -F "file=@portrait.jpg" \
  -F "style=vortex" \
  http://localhost:5000/api/crosshatch \
  -o output_vortex.jpg

# With custom max dimension
curl -X POST \
  -F "file=@portrait.jpg" \
  -F "style=horizontal" \
  -F "max_dimension=1500" \
  http://localhost:5000/api/crosshatch \
  -o output_large.jpg
```

### Python Client Example

```python
import requests

# Process image
with open('portrait.jpg', 'rb') as f:
    files = {'file': f}
    data = {'style': 'horizontal', 'max_dimension': '1200'}

    response = requests.post(
        'http://localhost:5000/api/crosshatch',
        files=files,
        data=data
    )

# Save result
if response.status_code == 200:
    with open('output.jpg', 'wb') as f:
        f.write(response.content)
    print("✓ Crosshatch created!")
else:
    print(f"Error: {response.json()}")
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function createCrosshatch(imagePath, outputPath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(imagePath));
  form.append('style', 'horizontal');
  form.append('max_dimension', '1200');

  const response = await axios.post(
    'http://localhost:5000/api/crosshatch',
    form,
    {
      headers: form.getHeaders(),
      responseType: 'arraybuffer'
    }
  );

  fs.writeFileSync(outputPath, response.data);
  console.log('✓ Crosshatch created!');
}

createCrosshatch('portrait.jpg', 'output.jpg');
```

## API Endpoints

### `GET /`
Returns API documentation and information.

### `GET /health`
Health check endpoint for monitoring.

### `POST /api/crosshatch`
Creates crosshatch effect on uploaded image.

**Parameters:**
- `file` (required): Image file (JPG, PNG)
- `style` (optional): `horizontal` or `vortex` (default: `horizontal`)
- `max_dimension` (optional): Maximum output dimension, 100-2400 (default: `1200`)

**Response:**
- Success: Returns crosshatched image (JPEG)
- Error: Returns JSON with error message

## Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `DEVICE` | Computing device | `cuda` | `cuda`, `cpu` |
| `SAM2_MODEL` | Model size | `small` | `tiny`, `small`, `base_plus`, `large` |
| `MAX_DIMENSION` | Default max dimension | `1200` | `100-2400` |
| `PORT` | API port | `5000` | Any valid port |

## Model Performance

### GPU (NVIDIA RTX 3080)

| Model | Speed | Quality | Memory |
|-------|-------|---------|--------|
| tiny | ~1.5s | Good | ~2GB |
| small | ~1.8s | Better | ~3GB |
| base_plus | ~2.5s | Great | ~4GB |
| large | ~3.5s | Best | ~6GB |

### CPU (Intel i9)

| Model | Speed | Quality | Memory |
|-------|-------|---------|--------|
| tiny | ~8s | Good | ~2GB |
| small | ~15s | Better | ~3GB |
| base_plus | ~30s | Great | ~4GB |
| large | ~60s | Best | ~6GB |

**Recommendation:**
- **GPU**: Use `small` or `base_plus` for best balance
- **CPU**: Use `tiny` for acceptable speed

## Testing

Use the provided test script:

```bash
# Test with an image
python docker-app/test_api.py portrait.jpg output.jpg horizontal

# The script will:
# 1. Check API health
# 2. Upload image and process
# 3. Download result
```

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml crosshatch

# Scale service
docker service scale crosshatch_crosshatch-api=3

# Check status
docker service ls
docker service logs crosshatch_crosshatch-api
```

### Using Kubernetes

See `k8s/` directory for Kubernetes manifests (coming soon).

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name crosshatch.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 20M;
        proxy_read_timeout 300s;
    }
}
```

## Monitoring

### Health Check

The API includes a health check endpoint that Docker uses:

```bash
# Check container health
docker ps

# Manual health check
curl http://localhost:5000/health
```

### Logs

```bash
# View logs
docker logs crosshatch-api

# Follow logs
docker logs -f crosshatch-api

# With docker-compose
docker-compose logs -f
```

### Metrics (Optional)

Add Prometheus metrics (coming soon):
- Request count
- Processing time
- Error rate
- Model inference time

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs crosshatch-api

# Common issues:
# 1. GPU not accessible
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 2. Port already in use
# Change port mapping: -p 5001:5000

# 3. Out of memory
# Use smaller model: -e SAM2_MODEL=tiny
```

### Slow processing

1. **Use GPU version** if available
2. **Reduce image size**: Set lower `max_dimension`
3. **Use smaller model**: `tiny` instead of `large`
4. **Check resources**: Ensure container has enough CPU/memory

### Poor segmentation quality

1. **Use larger model**: `large` or `base_plus`
2. **Better input images**: Well-lit, centered portraits
3. **Adjust parameters**: Try different styles

## Building for Different Architectures

### ARM64 (Apple Silicon, Raspberry Pi)

```bash
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile.cpu \
  -t crosshatch:2.0-arm64 \
  .
```

### Multi-platform

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t crosshatch:2.0-multiarch \
  --push \
  .
```

## Security Notes

- API has no authentication by default
- For production: Add API keys, rate limiting, HTTPS
- Uploaded files are temporarily stored and cleaned up
- Consider network isolation for production

## Contributing

See main [README.md](../README.md) for contribution guidelines.

## License

MIT License - see [LICENSE](../LICENSE) file.

## Support

- GitHub Issues: https://github.com/joeljose/Crosshatch/issues
- Documentation: https://github.com/joeljose/Crosshatch#readme

---

Made with ❤️ by [Joel Jose](https://github.com/joeljose)
