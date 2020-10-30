//-Ayan Chakrabarti <ayan.chakrabarti@gmail.com>

var cdiv = $('#cdiv');
var canvas = $('#canvas');
var img = $('#disp');
var dlist = $('#dlist');
var lstat = $('#lstat');

var dnames = [];
var smax = 0;
var skip = 0;
var scale = 50;

var cdrawing = false;
var x1=-1.0, x2=0.1, y1=0.9, y2=0.9;

// Ensure bounding box is within image.
const clamp = function() {
    if(x1 < 0) x1 = 0; if(x2 < 0) x2 = 0;
    if(y1 < 0) y1 = 0; if(y2 < 0) y2 = 0;
    if(x1 > 1.0) x1 = 1.0; if(x2 > 1.0) x2 = 1.0;
    if(y1 > 1.0) y1 = 1.0; if(y2 > 1.0) y2 = 1.0;
}

// Actually draw box.
const draw = function() {
    canvas[0].setAttribute('width', canvas.width());
    canvas[0].setAttribute('height', canvas.height());
    ctx = canvas[0].getContext('2d');
    ctx.clearRect(0, 0, canvas.width(), canvas.height());
    if(smax == 0) return;
    if(x1 < 0) return;
    ctx.beginPath();
    x1s = x1*img.width(); x2s = x2*img.width();
    y1s = y1*img.height(); y2s = y2*img.height();
    ctx.rect((x1s+img.offset().left-canvas.offset().left),
             (y1s+img.offset().top-canvas.offset().top),
             (x2s-x1s), (y2s-y1s));
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 5;
    ctx.stroke();
}

// Mouse down selects start of box.
const cmdown = function(e) {
    if(smax == 0)
        return false;
    if(!cdrawing) {
        cdrawing = true;
        x1 = (e.clientX - img.offset().left)/img.width();
        y1 = (e.clientY - img.offset().top)/img.height();
        x2=x1+0.01; y2=y1+0.01;
        clamp();
    } else
        return cmmove(e);
    return false;
}

// Mouse up freezes box position.
const cmup = function(e) {
    if(cdrawing) draw();
    cdrawing = false;
}

// Mouse move updated box.
const cmmove = function(e) {
    if(!cdrawing)
        return;
    x2 = (e.clientX - img.offset().left)/img.width();
    y2 = (e.clientY - img.offset().top)/img.height();
    clamp(); draw();
}

// Show a "scrolling" log of last 4 messages.
var thelogs = []; var logcount=0;
const log = function(msg) {
    thelogs = ["["+logcount+"] "+msg].concat(thelogs.slice(0,100));
    lstat.html(thelogs.join("<br />"));
    logcount++;
}

// Load new image (ensure previous image removed as new one loads).
const loadImg = function(url) {
    img[0].src = "";
    img[0].src = url;
};

// Run every time image has finished loading.
const imgupdate = function() {
    if(img[0].src != "")
        log(dnames[parseInt(dlist.val())] + "/" + skip
            + " : "
            + img[0].naturalWidth + "x" + img[0].naturalHeight);
    draw();
}

// Everytime we switch to a new directory
const dchange  = function() {
    smax = 0; loadImg(''); draw();
    $.ajax({type: 'GET', url: "/info/"+dlist.val(), dataType: 'json'})
     .done(function (resp) {
         smax = resp.smax;
         if(smax == 0) return;
         if(skip >= smax)
             skip = smax-1;
         if(resp.saved) {
             log("Loaded existing data for " + dnames[parseInt(dlist.val())]);
             skip = resp.skip; scale = resp.scale;
             x1 = resp.xlim[0]; x2 = resp.xlim[1];
             y1 = resp.ylim[0]; y2 = resp.ylim[1];
         } else
             x1 = -1.0;

         loadImg('/img/'+dlist.val()+':'+skip);
         $('#skip').html(""+skip);
         $('#scale').html(""+scale);
         cdrawing = false;
         draw();
     });
}

// Do actual save
const dosave = function() {
    if(smax == 0) return;
    if(x1 < 0) {log("Select ROI before saving."); return;}

    postOb = JSON.stringify({'skip': skip, 'scale': scale, 'xlim': [x1, x2], 'ylim': [y1, y2]});
    $.ajax({type: 'POST', url: "/save/"+dlist.val(), data: postOb, dataType: 'json'})
     .done(function (resp) {
         log(resp);
     });
}

//Update skip (call with -1 or +1)
const skupd = function(d) {
    if(smax == 0) return;
    if((d > 0 && skip < smax-1) || (d < 0 && skip > 0)) {
        skip = skip+d;
        $('#skip').html(""+skip);
        loadImg('/img/'+dlist.val()+':'+skip);
        cdrawing = false;
        draw();
    }
}

//Update scale (call with -1 or +1)
const scupd = function(d) {
    if(smax == 0) return;
    if(scale == 50 && d == 1)
        scale = 100;
    else if(scale == 50 && d == -1)
        scale = 25;
    else if(scale == 100 && d == -1)
        scale = 50;
    else if(scale == 25 && d == 1)
        scale = 50;
    $('#scale').html(""+scale);
}

// Update which sequence is selected
const dupd = function(d) {
    cval = parseInt(dlist.val());
    if(cval > 0 && d == -1)
        dlist.val(""+(cval-1)).change();
    else if(cval < dnames.length-1 && d == 1)
        dlist.val(""+(cval+1)).change();
}

// Get list of directories and initialize everything
const init = function() {
    $.ajax({type: 'GET', url: "/dlist", dataType: 'json'})
     .done(function (resp) {
         html = ''; dnames = resp;
         for(i = 0; i < dnames.length; i++)
             html = html + '<option value="'+i+'">'+dnames[i]+'</option>';
         dlist.html(html); dlist.val("0");
         dlist.change(dchange);
         dchange();
     });
}

$(document).ready(function() {
    cdiv.mousedown(cmdown);
    cdiv.mousemove(cmmove);
    cdiv.mouseup(cmup);

    $('#skminus').click(function() {skupd(-1);});
    $('#skplus').click(function() {skupd(1);});
    $('#scminus').click(function() {scupd(-1);});
    $('#scplus').click(function() {scupd(1);});
    $('#next').click(function() {dupd(1);});
    $('#prev').click(function() {dupd(-1);});
    $('#save').click(dosave);

    img.on("load", imgupdate);

    init();
});
