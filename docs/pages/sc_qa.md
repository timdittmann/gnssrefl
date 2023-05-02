# 2023 Short Course Zoom Webinar Q&A

## Tuesday Day 1

**Q: Can you guys please share the material via email?**

**A:** Yes, videos and slides will all be shared after the course.


**Q: Is polarization of L band GNSS, RHCP with respect to satellite or with respect to observer on earth?**

**A:** with respect to the direction of propagation


**Q: Are GNSS receivers equally sensitive to right and left handed polarized signals?**

**A:** antennas are built to prefer the right handed signals


**Q: What about antennas equiped with ground planes and/or choke rings? Can we use sites with these antennas for GNSS-IR?**

**A:** Yes


**Q: could GNSS-IR be used to estimate the precipitation in the columns above the receiver for the weather forecast?**

**A:** The direct signals are used to estimate tropospheric parameters (wet and dry delay)


**Q: What does the (W/W) metric mean?**

**A:** watts/watts


**Q: “5-ish meters is ideal” for measuring surface heights. Is there an upper elevation cutoff, say mounting an antenna on bedrock several hundred meters above an ocean surface for ocean tides?**

**A:** Yes, the upper bound of retrievable reflector height is defined by the multipath envelope: eg: https://www.researchgate.net/figure/Multipath-error-envelopes-of-GNSS-code-modulation-at-signal-multipath-ratio-of-6dB_fig8_26523309.


**Q: What is the effect of height of the antenna on the estimated moisture in GNSS-IR? Is there any optimal height you would recommend?**

**A:** mostly depends on how big you want your reflection zone to be.   i would never suggest going below 1 meter.  i have used 2 meters a lot for snow and soil moisture - but prefer taller for tides.


**Q: Can the code/phase observations be used instead of the SNR in GNSS-IR?**

**A:** Depends what you are trying to measure. Both phase and pseudorange are impacted by multipath, so in principle either are sensitive to the environment. But they are much more difficult to use than SNR data.


**Q: What is effect of orientation of the antenna on the estimated soil moisture in GNSS-IR?**

**A:** this software is only appropriate for a normal zenith pointing antenna.


**Q: For a receiver mounted on the roof top of a building, for example, on an iron sheet: Can I use GNSS-IR to measure corrosion?**

**A:** It'll be very hard unless the rust builds up enough to change the sheet thickness. I assume the metal conductivity won't change greatly with corrosion? Generally, it's easier to measure geometric changes than material composition changes.


**Q: How significant would objects that are small in area but high in elevation in the Fresnel zone affect the SNR?**

**A:** Tall objects are nasty because they might obstruct the direct line of sight to the satellite. But if it's an isolated object, like a single light pole, it won't affect most of the satellites most of the time. Unless it's really close to the antenna.


**Q: what role does salinity plat in the uncertainty of the height?**

**A:** Not much, as water salinity is more of a material composition property rather than a surface geometry property.


**Q: is it really recommended to calculate the sampling frequency beforehand depending on the height? what would happen if the set sampling frequency (e.g 1 sec) is higher than the calculated/ desired one (e.g 20 sec)?**

**A:** Higher sampling rate is always safer. So 1 second should suffice unless you're in a mountain top. You can always decimate the data to lower sampling rates to decrease file sizes and speed up data processing.


**Q: What does the height deviation term in the formula in the surface roughness slide indicate? Temporal height change, or spatial height change?**

**A:** Both spatial or temporal height changes ocurring during the ~ 1 hour making up a rising or setting satellite arc. Conversely, if the antenna mount pole is vibrating (vertically, not horizontally), that would be perceived as surface roughness.


**Q: Hi, nie pesentation. A short question. This LSP procedure is estimated through LSA? And a second one, the φ phase inside the equation is it known?**

**A:** LSSA and LSP are just different names given by geodesists and astronomers who reinvented the periodogram independently. The phase is generally unknown when doing the empirical fit to field data. It's only known in computer simulations.


**Q: Would thunderstorms interference data quality of GNSS-IR?consider that signal wave send from satellite may interference by lightning related plasma and sprite lightning.**

**A:** Intermittent LOS ‘interference’ could impact tracking and therefore SNR measurements, however recall these measurement arcs are accumulating energy over at least ~15-30 mins.


**Q: can one estimate snow properties laying on the antenna with your software and in principle. Hence, exploiting the direct signal instead of the reflected signal?**

**A:** Not with this software, which is using the reflected signal energy.


**Q: what is the approximate order of magnitude of the scale of roughness here ?**

**A:** It's the carrier wavelength, about 20 cm. Smaller scale will be random, larger scale will be systematic effect, affecting mean RH.


**Q: So far it seems like cheap antennas are better for GNSS-IR than expensive geodetic antennas. Is there a down side of using cheap antennas?**

**A:** Yes, cheaper navigation antennas are better than geodetic antennas for GNSS-IR. Their antenna phase center is not calibrated, though. However, in practice one is interested in the variations in water level over time. The absolute or geocentric height is more difficult. That's true even for geodetic antennas, because they're not calibrated for negative elevation angles.
Also, the cheap antennas are worse for positioning, for example you can't do precise point positioning with cheap antennas. the accurcacy of the vertical position tends to be particularly bad for cheap antennas

**Q: Is there a generalized criterion for selecting the maximum reflector height in LSP? For instance, Roesler and Larson (2018) set this value to be approximately 3 times the reflector height. However, should we calculate LSP up to 45 meters using the same approach for higher stations, e.g., a station with a height of 15 meters from the surface? Or should we cut off at a lower height value? Is there a criterion we can use for this?**

**A:** The best criterion is found using ancillary data such as site pictures or satellite photos. The 3x factor is used only when you have no idea what the antenna height is. In practice you'd want to narrow it interactively processing only one day. Then process all the days in the full series using the narrower limits.


**Q: Is there any SNR variation considering geology?**

**A:** Yes, assuming the rocks are exposed to air, like in an outcrop. Then the rock geometry will be the dominating geological property. But if it's covered with vegetation, then geology won't matter much.


**Q: so even if we use rinex 3 data we have to use the traditional rinex 3 nameing conventions?**

**A:**  Please see the files and formats section: https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html


**Q: If the antenna is not calibrated, is there any problem in the processing, derived from the antenna type not being in the header?**

**A:**  No problem, even if the antenna model is informed, it's not used in the data processing. That's a good idea for future improvements.
This is problematic for precise positioning and future developments of precision gnss-ir.


**Q: Is this possible to stack the periodogram of all passes to reduce the background noise and facilitate the detection of the reflection height?**

**A:**  Only if the antenna height is not changing during the stacking period. So it could be useful for snow but not for tides. The ground large-scale topography cannot be too great, otherwise the spectral peaks won't line up. Wind blows snow making it genuinely uneven around the antenna.


**Q: The RH is an average/median of all frequencies and all satellites?**

**A:**  Each rising and setting tracked signal within the processing criteria will estimate a reflector height.  Then the user decides what to do with these over time (ie: daily_avg() or sub_daily()) depending on the nature of the reflector you are interested in.


**Q: Why is crossing quadrants a problem? Or another way of asking my question, why is the analysis done by quandrant?**

**A:**  That's just the default settings, you can manually pick the azimuth quadrants to avoid the quadrant limits. It's only limited to 90 degree range per azimuth window. In future versions, this limit might be removed.


**Q: What is the advantage using high frequency data sampling over default 30s sampling?**  

**A:**  Higher frequency data enables larger reflector heights without aliasing.  This is related to the nyquist frequency estimation that Kristine mentioned:  a good reference is Roesler and Larson (2018) https://link.springer.com/article/10.1007/s10291-018-0744-8


**Q: Can you measure river widths from this code?**

**A:** not directly with this code, but you could potentially use GNSS-IR for this, depending on the geometry of the station relative to a river and in particular how wide the river is.  

**Q: Can I use helical antenna for GNSS-IR?**

**A:** Yes.