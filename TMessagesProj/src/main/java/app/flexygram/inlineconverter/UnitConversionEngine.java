/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;
import java.math.*;
public final class UnitConversionEngine {
    public static final class Result {public final BigDecimal value;public final String unit;Result(BigDecimal v,String u){value=v;unit=u;}}
    private static final MathContext MC=MathContext.DECIMAL128;
    private UnitConversionEngine(){}
    public static Result convert(BigDecimal value,String unit,boolean imperial){
        String base,target;BigDecimal factor;
        switch(unit){
            case "mile":case "miles":case "milla":case "millas":base="mi";target="km";factor=new BigDecimal("1.609344");break;
            case "km":case "kilometer":case "kilometers":case "kilómetro":case "kilómetros":case "kilometro":case "kilometros":base="km";target="mi";factor=BigDecimal.ONE.divide(new BigDecimal("1.609344"),MC);break;
            case "lb":case "lbs":case "pound":case "pounds":case "libra":case "libras":base="lb";target="kg";factor=new BigDecimal("0.45359237");break;
            case "kg":case "kilogram":case "kilograms":case "kilogramo":case "kilogramos":base="kg";target="lb";factor=BigDecimal.ONE.divide(new BigDecimal("0.45359237"),MC);break;
            case "ft":case "feet":case "foot":case "pies":base="ft";target="m";factor=new BigDecimal("0.3048");break;
            case "meter":case "meters":case "metro":case "metros":base="m";target="ft";factor=BigDecimal.ONE.divide(new BigDecimal("0.3048"),MC);break;
            case "inch":case "inches":case "pulgada":case "pulgadas":base="in";target="cm";factor=new BigDecimal("2.54");break;
            case "cm":case "centimeter":case "centimeters":case "centímetro":case "centímetros":base="cm";target="in";factor=BigDecimal.ONE.divide(new BigDecimal("2.54"),MC);break;
            case "°c":case "celsius":return imperial?new Result(value.multiply(new BigDecimal("1.8")).add(new BigDecimal("32")),"°F"):new Result(value,"°C");
            case "°f":case "fahrenheit":return imperial?new Result(value,"°F"):new Result(value.subtract(new BigDecimal("32")).divide(new BigDecimal("1.8"),MC),"°C");
            default:throw new IllegalArgumentException("Unknown unit");
        }
        boolean sourceImperial=base.equals("mi")||base.equals("lb")||base.equals("ft")||base.equals("in");
        return sourceImperial==imperial?new Result(value,base):new Result(value.multiply(factor,MC),target);
    }
}
