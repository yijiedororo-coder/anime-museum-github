'use strict';
// 按登记表同步插入专题脚本。新增专题不用改 index.html。
(function () {
  var sections = (window.MUSEUM_IP_REGISTRY && window.MUSEUM_IP_REGISTRY.sections) || [];
  var html = sections.map(function (section) {
    var file = section && section.file;
    if (!/^data\/[a-z0-9][a-z0-9./_-]*\.js$/.test(file || '')) return '';
    return '<script src="' + file + '"><\/script>';
  }).join('');
  document.write(html);
})();
