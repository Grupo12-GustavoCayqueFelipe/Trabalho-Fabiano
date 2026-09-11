function abrirPolitica() {
    document.getElementById("modalPolitica").style.display = "flex";
}

function fecharPolitica() {
    document.getElementById("modalPolitica").style.display = "none";
}

function salvarPreferencias() {
    const imagem = document.getElementById("imagem").checked;
    const whatsapp = document.getElementById("whatsapp").checked;

    alert(
        "Preferências salvas com sucesso!\n\n" +
        "Uso de imagem: " + (imagem ? "Autorizado" : "Não autorizado") + "\n" +
        "Comunicados por WhatsApp: " + (whatsapp ? "Autorizado" : "Não autorizado")
    );
}