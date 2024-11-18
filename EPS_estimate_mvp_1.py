

# region imports
from AlgorithmImports import *
from QuantConnect.DataSource import ExtractAlphaTrueBeats
# endregion

class EPSEstimates(QCAlgorithm):

    def Initialize(self):
        # Set Dates and Cash for the algorithm
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)
        
        # Set the equity object, symbol property, and EPS data
        self.equity = self.AddEquity("AAPL", Resolution.Daily)
        self.symbol = self.equity.Symbol
        self.eps_data = self.AddData(ExtractAlphaTrueBeats, self.symbol).Symbol

        # Set variables for the algorithm
        self.estimate_history = []  # List that will store the EPS data
        self.current_period = None  # Flag to verify the current period
        self.threshold = 0.2  # Growth Threshold
        self.min_data_points = 21  #  Data window size 


    def OnData(self, data: Slice):
        
        # Validate data extraction
        if data.ContainsKey(self.eps_data): 

            eps_data = data[self.eps_data]  # EPS slice object
            fiscal_period = eps_data.FiscalPeriod  # Fiscal period object
            fiscal_quarter = fiscal_period.FiscalQuarter  # Fiscar quarter 
            fiscal_year = fiscal_period.FiscalYear  # Fiscal year 
            expected_report_date = fiscal_period.ExpectedReportDate  # Expected report date 
            current_estimate = eps_data.EPS  #EPS Data-Point

            # Assign current fiscal year and quarter to update current period
            key_period = (fiscal_year, fiscal_quarter)


            # Verify the period and update
            if self.current_period is None or self.current_period != key_period: 
                self.Debug(f"Cambio a nuevo periodo fiscal: Q{fiscal_quarter} {fiscal_year}. Reiniciando datos")
                self.current_period = key_period
                self.estimate_history = []

            # Check if the company al ready published earnings
            if self.Time >= expected_report_date: 
                self.Debug(f"El periodo Q{fiscal_quarter} {fiscal_year} ya terminó. Esperando nuevo periodo fiscal.")
                return 

            # Add data points 
            if len(self.estimate_history) < self.min_data_points: 
                self.estimate_history.append(current_estimate)
                self.Debug(len(self.estimate_history))
                return 

            # Calculate EPS estimate growth 
            growth = (self.estimate_history[-1]/self.estimate_history[0]) - 1

            # Take positions if growth is greater than threshold
            if growth > self.threshold and not self.Portfolio.Invested: 
                self.SetHoldings(self.symbol, 0.1)
                self.Debug(f"Entrando en posición para Q{fiscal_quarter} {fiscal_year}. Crecimiento: {growth:.2%}")