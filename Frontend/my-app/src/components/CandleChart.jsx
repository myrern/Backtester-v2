import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
} from 'lightweight-charts';

export default function CandleChart() {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [barSizes, setBarSizes] = useState([]);
  const [selectedBarSize, setSelectedBarSize] = useState('');
  const containerRef = useRef(null);
  const chartRef     = useRef(null);
  const inited       = useRef(false);

  // Fetch symbols and bar sizes on mount
  useEffect(() => {
    axios.get('http://localhost:8000/metadata')
      .then(response => {
        const metadata = response.data;
        console.log('Metadata:', metadata); // Debug log for metadata
        console.log('Metadata type:', typeof metadata); // Debug log for metadata type
        console.log('Is array:', Array.isArray(metadata)); // Debug log for array check
        
        // Handle both object and array formats
        let symbolsList;
        if (Array.isArray(metadata)) {
          // If metadata is an array of symbol objects, extract the symbol names
          symbolsList = metadata.map(item => typeof item === 'string' ? item : Object.keys(item)[0]);
        } else {
          // If metadata is an object, get the keys (symbol names)
          symbolsList = Object.keys(metadata);
        }
        
        console.log('Symbols list:', symbolsList); // Debug log for symbols list
        setSymbols(symbolsList);
        
        if (selectedSymbol && metadata[selectedSymbol]) {
          setBarSizes(metadata[selectedSymbol].bar_sizes || []);
        }
      })
      .catch(error => console.error('Error fetching metadata:', error));
  }, []);

  // Fetch bar sizes when symbol changes
  useEffect(() => {
    if (!selectedSymbol) return;
    axios.get('http://localhost:8000/metadata')
      .then(response => {
        const metadata = response.data;
        console.log('Selected symbol:', selectedSymbol);
        console.log('Full metadata structure:', metadata);
        
        // Handle the array structure: [{AAPL: ["1 hour"]}, ...]
        let symbolData = null;
        if (Array.isArray(metadata)) {
          // Find the object that contains our symbol
          const symbolObject = metadata.find(item => item[selectedSymbol]);
          if (symbolObject) {
            symbolData = symbolObject[selectedSymbol];
          }
        } else {
          // Fallback for object structure
          symbolData = metadata[selectedSymbol];
        }
        
        console.log('Symbol data found:', symbolData);
        
        if (symbolData && Array.isArray(symbolData)) {
          // symbolData is directly the array of bar sizes
          console.log('Bar sizes for symbol:', symbolData);
          setBarSizes(symbolData);
        } else if (symbolData && symbolData.bar_sizes) {
          // symbolData is an object with bar_sizes property
          console.log('Bar sizes for symbol:', symbolData.bar_sizes);
          setBarSizes(symbolData.bar_sizes);
        } else {
          console.log('No symbol data found, setting empty bar sizes');
          setBarSizes([]);
        }
        setSelectedBarSize(''); // Reset bar size when symbol changes
      })
      .catch(error => console.error('Error fetching bar sizes:', error));
  }, [selectedSymbol]);

  // Chart effect: runs when symbol or bar size changes
  useEffect(() => {
    if (!selectedSymbol || !selectedBarSize) return;
    // clear any old DOM
    containerRef.current.innerHTML = '';

    (async () => {
      try {
        // fetch your JSON OHLCV
        const encodedBarSize = encodeURIComponent(selectedBarSize);
        const res  = await fetch(`http://127.0.0.1:8000/data/${selectedSymbol}?bar_size=${encodedBarSize}`);
        
        if (!res.ok) {
          console.error(`Failed to fetch data: ${res.status} ${res.statusText}`);
          return;
        }
        
        const data = await res.json();
        
        if (!Array.isArray(data)) {
          console.error('Data is not an array:', data);
          return;
        }
        
        const toUnix = t => Math.floor(new Date(t).getTime() / 1000);

      const ohlc = data.map(d => ({
        time:  toUnix(d.time),
        open:  d.open,
        high:  d.high,
        low:   d.low,
        close: d.close,
      }));
      const vols = data.map(d => ({
        time:  toUnix(d.time),
        value: d.volume,
      }));

      // createChart
      const chart = createChart(containerRef.current, {
        width:  800,
        height: 500,
        layout: {
          background: { color: '#ffffff' },
          textColor:  '#000000',
        },
        grid: {
          vertLines: { color: '#eeeeee' },
          horzLines: { color: '#eeeeee' },
        },
        timeScale: { timeVisible: true },
      });
      chartRef.current = chart;

      // 1) Candles go on default right scale:
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor:      '#26a69a',
        downColor:    '#ef5350',
        wickUpColor:  '#26a69a',
        wickDownColor:'#ef5350',
        borderVisible:false,
      });
      candleSeries.setData(ohlc);

      // 2) Volume gets its own new scale id "volume", and is only 15% tall:
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceScaleId:  'volume',       // <-- new scale
        scaleMargins: {
          top:    0.8,                 // reserve 80% for the candles
          bottom: 0.0,                 // volume starts from bottom
        },
        priceFormat: { 
          type: 'volume',
        },
        color: '#rgba(76, 175, 80, 0.3)', // Semi-transparent green
        base: 0,
      });
      
      // Make volume bars semi-transparent
      const volumeData = vols.map(d => ({
        time: d.time,
        value: d.value,
        color: d.close >= d.open ? 'rgba(38, 166, 154, 0.3)' : 'rgba(239, 83, 80, 0.3)', // Semi-transparent colors
      }));
      volumeSeries.setData(volumeData);

      chart.timeScale().fitContent();
      } catch (error) {
        console.error('Error fetching or processing chart data:', error);
      }
    })();

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [selectedSymbol, selectedBarSize]);

  const handleSymbolChange = (event) => {
    const symbol = event.target.value;
    setSelectedSymbol(symbol);
  };

  const handleRunBacktest = () => {
    if (!selectedSymbol || !selectedBarSize) {
      alert('Please select both a symbol and a bar size.');
      return;
    }

    // Fetch data for the selected symbol and bar size
    const encodedBarSize = encodeURIComponent(selectedBarSize);
    axios.get(`http://localhost:8000/data/${selectedSymbol}?bar_size=${encodedBarSize}`)
      .then(response => {
        console.log('Backtest data:', response.data);
        alert('Backtest data fetched successfully! Check the console for details.');
      })
      .catch(error => console.error('Error fetching backtest data:', error));
  };

  console.log('Symbols:', symbols); // Debug log for symbols array

  return (
    <div>
      <h1>Backtest Configuration</h1>

      <div>
        <label htmlFor="symbol">Select Symbol:</label>
        <select id="symbol" value={selectedSymbol} onChange={handleSymbolChange}>
          <option value="">-- Select a Symbol --</option>
          {symbols.map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
      </div>

      {barSizes.length > 0 && (
        <div>
          <label htmlFor="barSize">Select Bar Size:</label>
          <select id="barSize" value={selectedBarSize} onChange={(e) => setSelectedBarSize(e.target.value)}>
            <option value="">-- Select a Bar Size --</option>
            {barSizes.map(barSize => (
              <option key={barSize} value={barSize}>{barSize}</option>
            ))}
          </select>
        </div>
      )}

      <button onClick={handleRunBacktest}>Run Backtest</button>

      <div ref={containerRef} />
    </div>
  );
}
