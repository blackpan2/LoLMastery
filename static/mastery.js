/**
 * Created by Blackpan2 on 4/28/16.
 */
function toUpper() {
    var str = document.getElementById("upper").innerHTML;
    var first = str.slice(0,1);
    var second = str.slice(1);
    var res = first.toUpperCase() + second.toLowerCase();
    document.getElementById("upper").innerHTML = res;
}
