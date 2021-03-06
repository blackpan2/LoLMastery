/**
 * Copyright 2016 George Herde
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Created by Blackpan2 on 4/28/16.
 */
function toUpper() {
    var str = document.getElementById("upper").innerHTML;
    var first = str.slice(0, 1);
    var second = str.slice(1);
    document.getElementById("upper").innerHTML = first.toUpperCase() + second.toLowerCase();
}

/* Function to format a number with separators. returns formatted number.
 * num - the number to be formatted
 * decimal point - the decimal point character. if skipped, "." is used
 * sep - the separator character. if skipped, "," is used
 */
function FormatNumberBy3(num) {
    // check for missing parameters and use defaults if so
    var sep = ",";
    var decimal_point = ".";
    // need a string for operations
    num = num.toString();
    // separate the whole number and the fraction if possible
    var a = num.split(decimal_point);
    var x = a[0]; // decimal
    var y = a[1]; // fraction
    var z = "";
    if (typeof(x) != "undefined") {
        // reverse the digits. regexp works from left to right.
        for (var i = x.length - 1; i >= 0; i--)
            z += x.charAt(i);
        // add separators. but undo the trailing one, if there
        z = z.replace(/(\d{3})/g, "$1" + sep);
        if (z.slice(-sep.length) == sep)
            z = z.slice(0, -sep.length);
        x = "";
        // reverse again to get back the number
        for (i = z.length - 1; i >= 0; i--)
            x += z.charAt(i);
        // add the fraction back in, if it was there
        if (typeof(y) != "undefined" && y.length > 0)
            x += decimal_point + y;
    }
    return x;
}

function FormatNumberBy3Loop() {
    var formatList = document.getElementsByClassName("formatNumber3");
    for (var i = 0; i < formatList.length; i++) {
        document.getElementsByClassName("formatNumber3")[i].innerHTML =
            FormatNumberBy3(formatList[i].innerHTML);
    }
}

function championPicture() {
    var allChamps = document.getElementsByClassName("championPicture");
    for (var i = 0; i < allChamps.length; i++) {
        var name = allChamps[i].alt;
        document.getElementsByClassName("championPicture")[i].src = setChampionPicture(name);
    }
}

function setChampionPicture(name) {
    return "http://ddragon.leagueoflegends.com/cdn/6.9.1/img/champion/".concat(name).concat(".png");
}

function masteryIcon() {
    var allLevels = document.getElementsByClassName("mastery-icon");
    for (var i = 0; i < allLevels.length; i++) {
        var numeric = allLevels[i].alt;
        document.getElementsByClassName("mastery-icon")[i].src = "/static/images/tier" + numeric + ".png";
    }
}

function showAll() {
    $('.restrict-all').show()
}

function hideAll() {
    $('.restrict-all').hide()
}

function show0() {
    hideAll();
    $('.restrict-0').show()
}

function show1() {
    hideAll();
    $('.restrict-1').show()
}

function show2() {
    hideAll();
    $('.restrict-2').show()
}

function show3() {
    hideAll();
    $('.restrict-3').show()
}

function show4() {
    hideAll();
    $('.restrict-4').show()
}

function show5() {
    hideAll();
    $('.restrict-5').show()
}
