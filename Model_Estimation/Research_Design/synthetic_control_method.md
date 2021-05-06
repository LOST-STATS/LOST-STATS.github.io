---
title: Synthetic Control
parent: Research Design
grand_parent: Model Estimation
has_children: false
nav_order: 1
mathjax: true ## Switch to false if this page has no equations or other math rendering.
---

# Synthetic Control Method (SCM)

Synthetic Control Method is a way of estimating the causal effect of an intervention in comparative case studies. It is typically used with a small number of large units (e.g. countries, states, counties) to estimate the effects of aggregate interventions. The idea is to construct a convex combination of similar untreated units (often referred to as the "donor pool") to create a synthetic control that closely resembles the treatment subject and conduct counterfactual analysis with it.

We have $$j = 1, 2, ..., J+1$$ units, assuming without loss of generality that the first unit is the treated unit, $$Y_{1t}$$. Denoting the potential outcome without intervention as $$Y_{1t}^N$$, our goal is to estimate the treatment effect:

$$
\tau_{1t} = Y_{1t} - Y_{1t}^N
$$

We won't have data for $$Y_{1t}^N$$ but we can use synthetic controls to estimate it.

Let the $$k$$ x $$J$$ matrix $$X_0 = [X_2 ... X_{J+1}]$$ represent characteristics for the untreated units and the $$k$$-length vector $$X_1$$ represent characteristics for the treatment unit. Last, define our $$J\times 1$$ vector of weights as $$W = (w_2, ..., w_{J+1})'$$. Recall, these weights are used to form a convex combination of the untreated units. Now we have our estimate for the treatment effect:

$$
\hat{\tau_{1t}} = Y_{1t} - \hat{Y_{1t}^N}
$$

where $$\hat{Y_{1t}^N} = \sum_{j=2}^{J+1} w_j Y_{jt}$$.

The matrix of weights is found by choosing $$W*$$ to minimize
$$
\|X_1 - X_0W\|
$$
such that $$W >> 0$$ and $$\sum_2^{J+2} w_j = 1$$.

Once you've found the $$W*$$, you can put together an estimated $$\hat{Y_{1t}}$$ (synthetic control) for all time periods $$t$$. Because our synthetic control was constructed from untreated units, when the intervention occurs at time $$T_0$$, the difference between the synthetic control and the treated unit gives us our estimated treatment effect.

As a last bit of intuition, below is a graph depicting the upshot of the method. The synthetic control follows a very similar path to the treated unit pre-intervention. The difference between the two curves, post-intervention, gives us our estimated treatment effect. ![graph](../../Other/Images/scm-graph.jpg)

[Here](https://economics.mit.edu/files/17847) is an excellent resource by Alberto Abadie (the economist who developed the method) if you're interested in getting a more comprehensive overview of synthetic controls.

## Keep in Mind

- Unlike the [difference-in-difference](https://lost-stats.github.io/Model_Estimation/Research_Design/two_by_two_difference_in_difference.html) method, parallel trends aren't a necessary assumption. However, the donor pool must still share similar characteristics to the treatment unit in order to construct an accurate estimate.
- Panel data is necessary for the synthetic control method and, typically, requires observations over many time periods. Specifically, the pre-intervention time frame ought to be large enough to form an accurate estimate.
- Aggregate data is required for this method. Examples include state-level per-capita GDP, country-level crime rates, and state-level alcohol consumption statistics. Additionally, if aggregate data doesn't exist, you can sometimes aggregate micro-level data to estimate aggregate values.
- As a caveat to the previous bullet point, be wary of structural breaks when using large pre-intervention periods.
- [Abadie and L'Hour (2020)](https://economics.mit.edu/files/18642) also proposes a penalization method for performing the synthetic control method on disaggregated data.

## Also Consider

- As stated before, this technique can be compared to [difference-in-difference](https://lost-stats.github.io/Model_Estimation/Research_Design/two_by_two_difference_in_difference.html). If you don't have aggregate data or don't have sufficient data for the pre-intervention window and you have a control that you can confidently assume has a parallel trend to the treatment unit, then diff-in-diff might be better suited than SCM.

# Implementations

## R

To implement the synthetic control method in R, we will be using the package [Synth](https://cran.r-project.org/web/packages/Synth/Synth.pdf). While not used here, the **SynthTools** package also has a number of functions for making it easier to work with the **Synth** package. As stated above, the key part of the synthetic control method is to estimate the weight matrix $$W*$$ in order to form accurate estimates of the treatment unit. The Synth package provides you with the tools to find the weight matrix. From there, you can construct the synthetic control by interacting the $$W*$$ and the $Y$ values from the donor pool.

```r
# First we will load Synth and dplyr.
# If you haven't already installed Synth, now would be the time to do so

library(dplyr)
library(Synth)

# We're going to use simulated data included in the Synth package for our example.
# This dataframe consists of panel data including 1 outcome variable and 3 predictor variables for 1 treatment unit and 7 control units (donor pool) over 21 years

data("synth.data")

# The primary function that we will use is the synth() function.
# However, this function needs four particularly formed matrices as inputs, so it is highly recommended that you use the dataprep() function to generate the inputs.
# Once we've gathered our dataprep() output, we can just use that as our sole input for synth() and we'll be good to go.
# One important note is that your data must be in long format with id variables (integers) and name variables (character) for each unit.

dataprep_out <- dataprep(
  foo = synth.data, # first input is our data
  predictors = c("X1", "X2", "X3"), # identify our predictor variables
  predictors.op = "mean", # operation to be performed on the predictor variables for when we form our X_1 and X_0 matrices.
  time.predictors.prior = c(1984:1989), # pre-intervention window
  dependent = "Y", # outcome variable
  unit.variable = "unit.num", # identify our id variable
  unit.names.variable = "name", # identify our name variable
  time.variable = "year", # identify our time period variable
  treatment.identifier = 7, # integer that indicates the id variable value for our treatment unit
  controls.identifier = c(
    2, 13, 17, 29,
    32, 36, 38
  ), # vector that indicates the id variable values for the donor pool
  time.optimize.ssr = c(1984:1990), # identify the time period you want to optimize over to find the W*. Includes pre-treatment period and the treatment year.
  time.plot = c(1984:1996) # periods over which results are to be plotted with Synth's plot functions
)

# Now we have our data ready in the form of a list. We have all the matrices we need to run synth()
# Our output from the synth() function will be a list that includes our optimal weight matrix W*

synth_out <- dataprep_out %>% synth()

# From here, we can plot the treatment variable and the synthetic control using Synth's plot function.
# The variable tr.intake is an optional variable if you want a dashed vertical line where the intervention takes place.

synth_out %>% path.plot(dataprep.res = dataprep_out, tr.intake = 1990)

# Finally, we can construct our synthetic control variable if we wanted to conduct difference-in-difference analysis on it to estimate the treatment effect.

synth_control <- dataprep_out$Y0plot %*% synth_out$solution.w
```

## Stata

To implement the synthetic control method in Stata, we will be using the [synth](https://web.stanford.edu/~jhain/synthpage.html) and [synth_runner](https://github.com/bquistorff/synth_runner) packages. For a short tutorial on how to carry out the synthetic control method in Stata by Jens Hainmueller, there is a useful video [here](https://web.stanford.edu/~jhain/Video/SynthDemo.mp4).

```stata
*Install plottig graph scheme used below
ssc install blindschemes

*Install synth and synth_runner if they're not already installed (uncomment these to install)
* ssc install synth, all
* cap ado uninstall synth_runner //in-case already installed
* net install synth_runner, from(https://raw.github.com/bquistorff/synth_runner/master/) replace

*Import Dataset
sysuse synth_smoking.dta, clear

*Need to set the data as time series, using tsset
tsset state year
```

Next we will run the synthetic control analysis using synth_runner, which adds some useful options for estimation.

Note that this example uses the pre-treatment outcome for just three years (1988, 1980, and 1975), but any combination of pre-treatment outcome years can be specified. The `nested` option specifies a more computationally intensive but comprehensive method for estimating the synthetic control. The `trunit()` option specifies the ID of the treated entity (in this case, the state of California has an ID of 3).

```stata
synth cigsale beer lnincome retprice age15to24 cigsale(1988) ///
  cigsale(1980) cigsale(1975), trunit(3) trperiod(1989) fig ///
  nested keep(synth_results_data.dta) replace

/*Keeping the synth_results_data.dta stores a dataset of all the time series values of cigsale for each
  year for California (observed) and synthetic California (constructed using a weighted average of
  observed data from donor states). We can then import this dataset to create a synth plot whose
  attributes we can control. */
use synth_results_data.dta, clear
drop _Co_Number _W_Weight // Drops the columns of the data that store the donor state weights
twoway line (_Y_treated _Y_synthetic _time), scheme(plottig) xline(1989) ///
  xtitle(Year) ytitle(Cigarette Sales) legend(pos(6) rows(1))

** Run the analysis using synth_runner
*Import Dataset
sysuse synth_smoking.dta, clear

*Need to set the data as time series, using tsset
tsset state year

*Estimate Synthetic Control using synth_runner
synth_runner cigsale beer(1984(1)1988) lnincome(1972(1)1988) retprice age15to24 cigsale(1988) cigsale(1980) ///
  cigsale(1975), trunit(3) trperiod(1989) gen_vars
```

We can plot the effects in two ways: displaying both the treated and synthetic time series together and displaying the difference between the two over the time series. The first plot is equivalent to the plot produced by specifying the `fig` option for synth, except you can control aspects of the figure. For both plots you can control the plot appearence by specifying `effect_options()` or `tc_options()`, depending on which plot you would like to control.

```stata
effect_graphs, trlinediff(-1) effect_gname(cigsale1_effect) tc_gname(cigsale1_tc) ///
	effect_options(scheme(plottig)) tc_options(scheme(plottig))

/*Graph the outcome paths of all units and (if there is only one treated unit)
	a second graph that shows prediction differences for all units
*/
single_treatment_graphs, trlinediff(-1) raw_gname(cigsale1_raw) ///
	effects_gname(cigsale1_effects) effects_ylabels(-30(10)30) ///
	effects_ymax(35) effects_ymin(-35)
```

