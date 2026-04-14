#!/bin/bash

set -e

echo "=============================="
echo "Atualizando sistema"
echo "=============================="
sudo apt update

echo "=============================="
echo "Instalando dependencias base"
echo "=============================="
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    curl \
    unzip

echo "=============================="
echo "Clonando repositorio"
echo "=============================="

if [ ! -d "nat_data" ]; then
    git clone https://github.com/Hakeera/nat_data.git
else
    echo "Repositorio já existe, pulando clone"
fi

echo "=============================="
echo "Entrando no projeto"
echo "=============================="
cd nat_data

echo "=============================="
echo "Permissões de execução"
echo "=============================="
chmod +x setup.sh
chmod +x run_revista.sh
chmod +x run_cpf.sh

echo "=============================="
echo "Rodando setup do projeto"
echo "=============================="
./setup.sh

echo "=============================="
echo "Teste rápido"
echo "=============================="
./run_revista.sh 05

echo "=============================="
echo "INSTALAÇÃO FINALIZADA"
echo "=============================="
