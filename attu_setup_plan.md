# 添加 Attu（Milvus Web GUI）到 Docker Compose

## 一、总结

在现有 docker-compose.yml 中添加 Attu 服务，通过浏览器访问 Milvus 数据。无需修改代码。

## 二、当前状态

- Milvus 已运行（etcd + minio + standalone）
- 无图形化管理界面
- Attu 官方镜像 `zilliz/attu:latest`，默认端口 3000

## 三、变更

### 文件：`agentflow/docker/docker-compose.yml`

在 `standalone` 服务后添加 Attu 服务：

```yaml
  attu:
    container_name: milvus-attu
    image: zilliz/attu:latest
    ports:
      - "3000:3000"
    environment:
      MILVUS_HOST: standalone
      MILVUS_PORT: "19530"
    depends_on:
      standalone:
        condition: service_healthy
```

连接参数：`host=standalone`（Docker 内部 DNS 解析到 milvus-standalone），无需外部 IP。

## 四、验证步骤

1. `docker compose -f docker/docker-compose.yml up -d`（或 `start.bat`）
2. 浏览器打开 `http://localhost:3000`
3. Attu 自动连接 Milvus，无需手动输入地址
4. 可查看集合 `agentflow_chunks`、向量数据、索引状态
