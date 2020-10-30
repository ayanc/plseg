//-Ayan Chakrabarti <ayan.chakrabarti@gmail.com>

var base = $('#base');
var seg = $('#segs');
var dlist = $('#dlist');
var lstat = $('#lstat');
var canvas = $('#canvas')

var dnames = [];
var imgid = 0;
var iidmax = 0;
var todel = [];


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
    if(!cdrawing) return;
    ctx.beginPath();
    x1s = x1*base.width(); x2s = x2*base.width();
    y1s = y1*base.height(); y2s = y2*base.height();
    ctx.rect((x1s+base.offset().left-canvas.offset().left),
             (y1s+base.offset().top-canvas.offset().top),
             (x2s-x1s), (y2s-y1s));
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 5;
    ctx.stroke();
}

// Mouse down selects start of box.
const cmdown = function(e) {
    if(iidmax == 0) {cdrawing = 0; draw(); return false;}
    if(!cdrawing) {
        cdrawing = true;
        x1 = (e.clientX - base.offset().left)/base.width();
        y1 = (e.clientY - base.offset().top)/base.height();
        x2=x1+0.01; y2=y1+0.01;
        clamp();
    } else
        return cmmove(e);
    return false;
}

// Mouse up freezes box position.
const cmup = function() {
    if(cdrawing) {
        if(x1 < x2) {
            xl = x1*base[0].naturalWidth;
            xr = x2*base[0].naturalWidth;
        } else {
            xl = x2*base[0].naturalWidth;
            xr = x1*base[0].naturalWidth;
        }
        if(y1 < y2) {
            yl = y1*base[0].naturalHeight;
            yr = y2*base[0].naturalHeight;
        } else {
            yl = y2*base[0].naturalHeight;
            yr = y1*base[0].naturalHeight;
        }

        url = "/getlabel/" + [imgid, parseInt(yl),
                              parseInt(yr), parseInt(xl),
                              parseInt(xr)].join(":");
        $.ajax({type: 'GET', url: url, dataType: 'json'})
         .done(function (resp) {
             resp.label.forEach(toggleDel);
         });
    }
    cdrawing = false; draw();
}

// Mouse move updated box.
const cmmove = function(e) {
    if(!cdrawing)
        return;
    x2 = (e.clientX - base.offset().left)/base.width();
    y2 = (e.clientY - base.offset().top)/base.height();
    clamp(); draw();
}

// Show a "scrolling" log of last 4 messages.
var thelogs = []; var logcount=0;
const log = function(msg) {
    thelogs = ["["+logcount+"] "+msg].concat(thelogs.slice(0,100));
    lstat.html(thelogs.join("<br />"));
    logcount++;
}

// Toggle label from deletion set
const toggleDel = function(lbl) {
    idx = todel.indexOf(lbl);
    if(idx == -1) {
        todel.push(lbl);
        log("Deleting label " + lbl);
    } else {
        todel.splice(idx, 1);
        log("Un-Deleting label " + lbl);
    }
    loadImg();
}

// Save data
const save = function() {
    log("Saving ...");
    url = "/save/:" + todel.sort((a,b) => a-b).join(":");
    $.ajax({type: 'GET', url: url})
     .done(function () {
         log("Saved!");
     });
}

// Load new image (ensure previous image removed as new one loads).
const loadImg = function() {
    $("#imgid").html(""+imgid);
    base[0].src = "";
    seg[0].src = "";
    if(iidmax > 0) {
        base[0].src = "/img/"+ dlist.val() + ":" + imgid;
        if(todel.length == 0)
            seg[0].src = "/seg/" + dlist.val() + ":" + imgid;
        else
            seg[0].src = "/seg/" + dlist.val() + ":" + imgid + ":"
            + todel.sort((a,b) => a-b).join(":");
    }
}

// Everytime we switch to a new directory
const dchange  = function() {
    base[0].src = ""; seg[0].src = "";
    log("Loading data for " + dnames[parseInt(dlist.val())]);
    $.ajax({type: 'GET', url: "/load/"+dlist.val(), dataType: 'json'})
     .done(function (resp) {
         iidmax = resp.numi;
         imgid = iidmax-1;
         if(resp.saved) {
             todel = resp.removed;
             log("Done loading, previously saved file found.");
         } else {
             todel = [];
             log("Done loading, no previous saved data.")
         }
         loadImg();
     });
}

// Update which sequence is selected
const dupd = function(d) {
    cval = parseInt(dlist.val());
    if(cval > 0 && d == -1)
        dlist.val(""+(cval-1)).change();
    else if(cval < dnames.length-1 && d == 1)
        dlist.val(""+(cval+1)).change();
}

// Update which sequence is selected
const imupd = function(d) {
    imgid = imgid + d;
    if(imgid < 0) imgid = 0;
    if(imgid >= iidmax) imgid = iidmax-1;
    loadImg();
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
    $("#cdiv").mousedown(cmdown);
    $("#cdiv").mousemove(cmmove);
    $("#cdiv").mouseup(cmup);
    $('#next').click(function() {dupd(1);});
    $('#prev').click(function() {dupd(-1);});

    $('#skm1').click(function() {imupd(-1);});
    $('#skm10').click(function() {imupd(-10);});
    $('#skp1').click(function() {imupd(1);});
    $('#skp10').click(function() {imupd(10);});

    $('#save').click(save);

    $('#tseg').change(function () {
        if($('#tseg')[0].checked) seg.removeClass('d-none'); else seg.addClass('d-none');
    });

    init();
});
