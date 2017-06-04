#encoding "utf8"

DayNum -> AnyWord<wff=/([1-2]?[0-9])|(3[0-1])/>;
Day -> DayNum;

Month-> Noun<kwtype="месяц">;

YearNum -> AnyWord<wff=/[1-2][0-9][0-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9]|[1-9]/>;
YearDef -> "год" | "г" Punct | "гг" Punct;
YearBC -> "донэ";
YearDescr -> YearDef | YearBC interp (Date.IsBC) | YearDef YearBC interp (Date.IsBC);
Year -> YearNum (YearDescr);

Date-> Day interp (Date.Day) Month interp (Date.Month) YearNum interp (Date.Year) (YearDescr)
	| Month interp (Date.Month) YearNum interp (Date.Year) (YearDescr)
	| YearNum interp (Date.Year) YearDescr;

HyphenDescr -> Hyphen | '-';

DateInterval -> (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
                    HyphenDescr interp (Date.IsInterval)
                (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
	| (Day interp (Date.Day)) Month interp (Date.Month)
	        HyphenDescr interp (Date.IsInterval)
	  (Day interp (Date.Day)) Month interp (Date.Month)
	| (Day interp (Date.Day)) Month interp (Date.Month)
	        HyphenDescr interp (Date.IsInterval)
	  (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
	| Day interp (Date.Day)
	        HyphenDescr interp (Date.IsInterval)
	  Day interp (Date.Day) Month interp (Date.Month)
	| Day interp (Date.Day)
	        HyphenDescr interp (Date.IsInterval)
	  Day interp (Date.Day) Month interp (Date.Month) Year interp (Date.Year)
	| Year interp (Date.Year)
	        HyphenDescr interp (Date.IsInterval)
	  Year interp (Date.Year)
	
	| "с" (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
	            "по" interp (Date.IsInterval)
		  (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
	| "с" (Day interp (Date.Day)) Month interp (Date.Month)
	            "по" interp (Date.IsInterval)
		  (Day interp (Date.Day)) Month interp (Date.Month)
	| "с" (Day interp (Date.Day)) Month interp (Date.Month)
	            "по" interp (Date.IsInterval)
		  (Day interp (Date.Day)) Month interp (Date.Month) Year interp (Date.Year)
	| "с" Day interp (Date.Day)
	        "по" interp (Date.IsInterval)
	      Day interp (Date.Day) Month interp (Date.Month)
	| "с" Day interp (Date.Day)
	        "по" interp (Date.IsInterval)
	      Day interp (Date.Day) Month interp (Date.Month) Year interp (Date.Year)
	| "с" Year interp (Date.Year)
	        "по" interp (Date.IsInterval)
	      Year interp (Date.Year);

AnyDate -> Date | DateInterval;