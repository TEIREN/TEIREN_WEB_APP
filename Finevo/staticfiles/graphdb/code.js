/* global Promise, fetch, window, cytoscape, document, tippy, _ */

$(document).ready(function(){
Promise.all([
  fetch('/staticfiles/graphdb/cy-styles.json')
    .then(function(res) {
      return res.json();
    }),
  detect_json
])
  .then(function(dataArray) {
    var h = function(tag, attrs, children){
      var el = document.createElement(tag);
      Object.keys(attrs).forEach(function(key){
        var val = attrs[key];

        el.setAttribute(key, val);
      });

      children.forEach(function(child){
        el.appendChild(child);
      });

      return el;
    };

    var t = function(text){
      var el = document.createTextNode(text);

      return el;
    };

    var $ = document.querySelector.bind(document);

    var cy = window.cy = cytoscape({
      container: document.getElementById('cy'),
      style: dataArray[0],
      elements: dataArray[1],
      layout: { name: 'circle' },
    });
    // var params = {
    //   name: 'euler',
    //   nodeSpacing: 25,
    //   edgeLengthVal: 150,
    //   animate: true,
    //   randomize: false,
    //   maxSimulationTime: 1500
    // };
    var cur_edgeLength = {
      cur: 100,
      max: 200
    }
    var gravity = {
      cur: -500,
      max: -100,
      min: -900,
    }
    var params = {
      name: 'euler',
      randomize: false,
      fit: true,
      animate: 'end',
      animationDuration: 600,
      gravity: gravity['cur'],
      springLength: cur_edgeLength['cur'],
      // maxSimulationTime: maxsim,
      springCoeff: 0.0002,
      mass: function() { return 1; },
      pull: 0.001,
      iterations: 2500
    };
    var layout = makeLayout();

    layout.run();

    var $btnParam = h('div', {
      'class': 'param'
    }, []);

    var $config = $('#config');

    $config.appendChild( $btnParam );

    // var sliders = [
    //   {
    //     label: 'Edge length',
    //     param: 'edgeLengthVal',
    //     min: 100,
    //     max: 200
    //   },

    //   {
    //     label: 'Node spacing',
    //     param: 'nodeSpacing',
    //     min: 1,
    //     max: 50
    //   }
    // ];
    var sliders = [
      {
        label: 'Edge length',
        param: 'springLength',
        min: 0,
        max: cur_edgeLength['max']
      },
      {
        label: 'Node spacing',
        param: 'gravity',
        min: gravity['min'],
        max: gravity['max']
      },
    ];
    
    var buttons = [
      {
        label: h('span', { 'class': 'fa fa-refresh' }, []),
        layoutOpts: {
          flow: { axis: 'x', minSeparation: 1 }
        }
      },

      {
        label: h('span', { 'class': 'fa fa-long-arrow-down' }, []),
        layoutOpts: {
          flow: { axis: 'y', minSeparation: 30 }
        }
      }
    ];

    sliders.forEach( makeSlider );

    buttons.forEach( makeButton );

    function makeLayout( opts ){
      params.randomize = false;
      params.edgeLength = function(e){ return params.edgeLengthVal / e.data('weight'); };
      for( var i in opts ){
        params[i] = opts[i];
      }

      return cy.layout( params );
    }

    function makeSlider( opts ){
      var $input = h('input', {
        id: 'slider-'+opts.param,
        type: 'range',
        min: opts.min,
        max: opts.max,
        step: 1,
        value: params[ opts.param ],
        'class': 'slider'
      }, []);

      var $param = h('div', { 'class': 'param' }, []);

      var $label = h('label', { 'class': 'label label-default', for: 'slider-'+opts.param }, [ t(opts.label) ]);

      $param.appendChild( $label );
      $param.appendChild( $input );

      $config.appendChild( $param );

      var update = _.throttle(function(){
        params[ opts.param ] = $input.value;

        layout.stop();
        layout = makeLayout();
        layout.run();
      }, 1000/30);

      $input.addEventListener('input', update);
      $input.addEventListener('change', update);
    }

    function makeButton( opts ){
      var $button = h('button', { 'class': 'btn btn-default' }, [ opts.label ]);

      $btnParam.appendChild( $button );

      $button.addEventListener('click', function(){
        layout.stop();

        if( opts.fn ){ opts.fn(); }

        layout = makeLayout( opts.layoutOpts );
        layout.run();
      });
    }

    var makeTippy = function(node, html){
      return tippy( node.popperRef(), {
        html: html,
        trigger: 'manual',
        arrow: true,
        placement: 'bottom',
        hideOnClick: false,
        interactive: true
      } ).tooltips[0];
    };

    var hideTippy = function(node){
      var tippy = node.data('tippy');

      if(tippy != null){
        tippy.hide();
      }
    };

    var hideAllTippies = function(){
      cy.nodes().forEach(hideTippy);
    };

    cy.on('tap', function(e){
      if(e.target === cy){
        hideAllTippies();
      }
    });

    cy.on('tap', 'edge', function(e){
      hideAllTippies();
    });

    cy.on('zoom pan', function(e){
      hideAllTippies();
    });

    cy.nodes().forEach(function(n){
      if (n.data('label') == 'LOG'){
        var $data = []
        for(var i in n.data()){
          if (i == 'score' || i == 'query' || i == 'gene'){
            continue;
          }
          if (i == 'id'){var x = {name: 'NodeId: '+n.data(i)}}
          else if (i == 'userAgent'){var x = {name: i+':'+n.data(i)}}
          else{var x = {name:i+': '+n.data(i)}}
          $data.push(x)
        }
      }
      else {
        var $data = []
        for(var i in n.data()){
          if (i == 'score' || i == 'query' || i == 'gene'){
            continue;
          }
          if (i == 'id'){var x = {name: 'NodeId: '+n.data(i)}}
          else{var x = {name:i+': '+n.data(i)}}
          $data.push(x)
        }
      }
      var $properties = $data.map(function( property ){
        return h('div', {class:'mb-1 text-left'}, [ t(property.name) ]);
      });

      var tippy = makeTippy(n, h('div', {}, $properties));

      n.data('tippy', tippy);

      n.on('click', function(e){
        tippy.show();

        cy.nodes().not(n).forEach(hideTippy);
      });
    });

    $('#config-toggle').addEventListener('click', function(){
      $('body').classList.toggle('config-closed');

      cy.resize();
    });

  });
  setTimeout(() => {
      $('#slider-edgeLengthVal').on('input', function() {
          var value = Number($(this).val())-this.min;
          var gradient = 'linear-gradient(to right, #6AB3CF 0%, #26486B ' + value + '%, #6E7D8C ' + value + '%, #9c9ea0 100%)';
          $(this).css('background', gradient)
      });
      $('#slider-nodeSpacing').on('input', function() {
          var value = Number($(this).val())*2;
          var gradient = 'linear-gradient(to right, #6AB3CF 0%, #26486B ' + value + '%, #6E7D8C ' + value + '%, #9c9ea0 100%)';
          $(this).css('background', gradient)
      });
  }, 1000);
});
