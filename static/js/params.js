function addParameter() {
    let param_name = prompt("Что за параметр?", "дальность");
    let form = document.getElementById("inputs");
    let dependency_selector = param_name + ': <select name="' + param_name + '">' +
        '<option value="lin">Прямая</option>' +
        '<option value="sqr">Квадрат</option>' +
        '<option value="div">Обратная</option>' +
        '<option value="dsq">Обратный квадрат</option>' +
        '<option value="exp">Экспонента</option> </select>';
    form.insertAdjacentHTML("beforeend", dependency_selector)
}